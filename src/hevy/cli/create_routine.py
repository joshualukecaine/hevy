#!/usr/bin/env python3
"""Create workout routines in Hevy from JSON files.

Converts structured workout programs into Hevy routines,
with support for supersets, circuits, and validation.

Usage:
    hevy-create --input workout.json [--validate-only] [--folder NAME]
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from hevy.api import HevyAPIError, HevyClient
from hevy.cli.logging_config import setup_logging
from hevy.core import TemplateCache, ValidationError, validate_program
from hevy.models import Routine, WorkoutProgram

logger = logging.getLogger(__name__)

DEFAULT_INPUT = "./examples/routines/runner_program.json"
DEFAULT_CACHE_PATH = "./data/exercise_templates.json"


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Create workout routines in Hevy from JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    hevy-create --input workout.json
    hevy-create --input workout.json --validate-only
    hevy-create --input workout.json --folder "My Program"
    hevy-create --input workout.json --title "Week 1"

Superset/Circuit Support:
    Your JSON can include supersets and circuits:

    Regular exercise:
        {"name": "Push Up", "exercise_template_id": "392887AA", "sets": 3, "reps": 10}

    Superset (2+ exercises back-to-back):
        {
            "superset": {
                "exercises": [
                    {"name": "Push Up", "exercise_template_id": "392887AA", "sets": 3, "reps": 10},
                    {"name": "Pull Up", "exercise_template_id": "ABC12345", "sets": 3, "reps": 8}
                ]
            }
        }

    Circuit (multiple rounds):
        {
            "circuit": {
                "rounds": 3,
                "exercises": [
                    {"name": "Burpees", "exercise_template_id": "DEF67890", "reps": 10},
                    {"name": "Squats", "exercise_template_id": "GHI11111", "reps": 15}
                ]
            }
        }
        """,
    )
    parser.add_argument(
        "--input",
        "-i",
        default=DEFAULT_INPUT,
        help=f"Path to the routine JSON file (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--title",
        "-t",
        default="",
        help="Base title prefix for routines",
    )
    parser.add_argument(
        "--notes",
        "-n",
        default="Created via Hevy CLI",
        help="Notes to add to routines",
    )
    parser.add_argument(
        "--folder",
        "-f",
        help="Custom folder name (defaults to program_name or timestamp)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the routine without creating it",
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Automatically apply first suggested fix for invalid exercises",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    return parser


def load_program(input_path: str) -> WorkoutProgram:
    """Load and parse a workout program from JSON.

    Args:
        input_path: Path to the JSON file

    Returns:
        Parsed WorkoutProgram

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    return WorkoutProgram.from_json(data)


def print_validation_errors(errors: list[ValidationError]) -> None:
    """Print formatted validation errors."""
    print("\n❌ Found invalid exercises:")
    for error in errors:
        print(f"\n  {error.day_name} - {error.exercise_name}")
        print(f"    ID: {error.template_id}")
        print(f"    Reason: {error.reason}")
        if error.alternatives:
            print(f"    Suggestions: {', '.join(a.title for a in error.alternatives[:3])}")


def interactive_fix(
    errors: list[ValidationError],
    program_data: dict,
    input_path: str,
) -> bool:
    """Interactively fix validation errors.

    Args:
        errors: List of validation errors
        program_data: Raw program data to modify
        input_path: Path to save updated file

    Returns:
        True if changes were made
    """
    print("\nOptions:")
    print("  y    - Fix exercises one by one")
    print("  auto - Use first suggestion for all")
    print("  n    - Skip fixing")

    choice = input("\nWhat would you like to do? ").lower().strip()

    if choice == "n":
        return False

    changes_made = False

    if choice == "auto":
        for error in errors:
            if error.alternatives:
                alt = error.alternatives[0]
                program_data["days"][error.day_index]["exercises"][error.exercise_index][
                    "exercise_template_id"
                ] = alt.id
                print(f"Fixed {error.exercise_name} with {alt.title}")
                changes_made = True

    elif choice == "y":
        for error in errors:
            if not error.alternatives:
                print(f"\nSkipping {error.exercise_name} (no alternatives)")
                continue

            print(f"\nFixing {error.exercise_name} in {error.day_name}...")
            print("Available alternatives:")
            for i, alt in enumerate(error.alternatives[:10], 1):
                print(f"  {i}. {alt.title}")

            print("\nEnter number to select, or press Enter to skip:")
            selection = input().strip()

            if selection:
                try:
                    idx = int(selection) - 1
                    if 0 <= idx < len(error.alternatives):
                        alt = error.alternatives[idx]
                        program_data["days"][error.day_index]["exercises"][error.exercise_index][
                            "exercise_template_id"
                        ] = alt.id
                        print(f"Fixed with {alt.title}")
                        changes_made = True
                except ValueError:
                    print("Invalid selection, skipping")

    if changes_made:
        print(f"\nSaving updated routine to {input_path}...")
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(program_data, f, indent=4)
        print("Routine updated successfully!")

    return changes_made


def main(args: list[str] | None = None) -> int:
    """Main entry point for the create-routine command.

    Args:
        args: Command line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    setup_logging(verbose=parsed_args.verbose)

    mode = "validation" if parsed_args.validate_only else "creation"
    print(f"Starting routine {mode} from {parsed_args.input}...")

    try:
        # Load program
        program = load_program(parsed_args.input)
        print(f"Loaded program: {program.program_name} ({len(program.days)} days)")

        # Load templates for validation
        cache = TemplateCache(DEFAULT_CACHE_PATH)
        if not cache.exists():
            print("Warning: Template cache not found. Run 'hevy-fetch' first for validation.")
            templates = []
        else:
            templates = cache.load()

        # Validate
        if templates:
            result = validate_program(program, templates)

            if not result.is_valid:
                print_validation_errors(result.errors)

                if parsed_args.auto_fix:
                    # Load raw data for modification
                    with open(parsed_args.input, encoding="utf-8") as f:
                        raw_data = json.load(f)

                    for error in result.errors:
                        if error.alternatives:
                            alt = error.alternatives[0]
                            raw_data["days"][error.day_index]["exercises"][error.exercise_index][
                                "exercise_template_id"
                            ] = alt.id
                            print(f"Auto-fixed {error.exercise_name} with {alt.title}")

                    with open(parsed_args.input, "w", encoding="utf-8") as f:
                        json.dump(raw_data, f, indent=4)

                    # Reload and revalidate
                    program = load_program(parsed_args.input)
                    result = validate_program(program, templates)

                if not result.is_valid:
                    print("\n❌ Validation failed. Fix the errors and try again.")
                    return 1

        if parsed_args.validate_only:
            print("\n✓ Validation passed! All exercises are valid.")
            return 0

        # Create routines
        client = HevyClient.from_env()

        # Create folder
        folder_name = (
            parsed_args.folder
            or program.program_name
            or f"Routines {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        print(f"\nCreating routine folder '{folder_name}'...")
        folder_id = client.create_routine_folder(folder_name)
        print(f"Folder created with ID: {folder_id}")

        # Create routines for each day
        routine_ids = []
        for day in program.days:
            routine = Routine.from_workout_day(
                day=day,
                base_title=parsed_args.title,
                notes=parsed_args.notes,
                folder_id=folder_id,
            )

            print(f"Creating routine '{routine.title}'...")
            routine_id = client.create_routine(routine)
            routine_ids.append(routine_id)
            print(f"  Created with ID: {routine_id}")

        print(f"\n✓ Done! Created {len(routine_ids)} routines in folder '{folder_name}'.")
        return 0

    except FileNotFoundError as e:
        logger.error("File not found: %s", e)
        print(f"Error: {e}")
        return 1

    except json.JSONDecodeError as e:
        logger.error("Invalid JSON: %s", e)
        print(f"Error: Invalid JSON in input file - {e}")
        return 1

    except HevyAPIError as e:
        logger.error("API error: %s", e)
        print(f"Error: {e}")
        return 1

    except Exception as e:
        logger.exception("Unexpected error")
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
