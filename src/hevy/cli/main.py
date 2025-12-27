#!/usr/bin/env python3
"""Main CLI entry point for the Hevy toolkit.

Provides a unified interface for all Hevy CLI commands.

Usage:
    hevy fetch [--force]
    hevy create --input workout.json
    hevy validate --input workout.json
"""

import argparse
import sys

from hevy import __version__
from hevy.cli import create_routine, fetch_templates
from hevy.cli.logging_config import setup_logging


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="hevy",
        description="CLI toolkit for interacting with the Hevy workout app API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
    fetch     Download exercise templates from Hevy
    create    Create routines from JSON files
    validate  Validate a routine file without creating it

Examples:
    hevy fetch --force
    hevy create --input workout.json
    hevy create --input workout.json --validate-only
    hevy validate --input workout.json

For more information on a specific command:
    hevy <command> --help
        """,
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"hevy-cli {__version__}",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Fetch command
    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Download exercise templates from Hevy API",
        description="Fetch and cache exercise templates for offline use",
    )
    fetch_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force update even if cache is recent",
    )
    fetch_parser.add_argument(
        "--output",
        "-o",
        default="./data/exercise_templates.json",
        help="Output file path",
    )

    # Create command
    create_parser = subparsers.add_parser(
        "create",
        help="Create routines in Hevy from JSON files",
        description="Convert workout programs to Hevy routines",
    )
    create_parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to the routine JSON file",
    )
    create_parser.add_argument(
        "--title",
        "-t",
        default="",
        help="Base title prefix for routines",
    )
    create_parser.add_argument(
        "--notes",
        "-n",
        default="Created via Hevy CLI",
        help="Notes to add to routines",
    )
    create_parser.add_argument(
        "--folder",
        "-f",
        help="Custom folder name",
    )
    create_parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate without creating",
    )
    create_parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Auto-fix invalid exercises",
    )

    # Validate command (shortcut for create --validate-only)
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a routine file",
        description="Check a routine file for errors without creating it",
    )
    validate_parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to the routine JSON file",
    )

    return parser


def main(args: list[str] | None = None) -> int:
    """Main entry point for the Hevy CLI.

    Args:
        args: Command line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    setup_logging(verbose=parsed_args.verbose)

    if not parsed_args.command:
        parser.print_help()
        return 0

    if parsed_args.command == "fetch":
        fetch_args = ["--output", parsed_args.output]
        if parsed_args.force:
            fetch_args.append("--force")
        if parsed_args.verbose:
            fetch_args.append("--verbose")
        return fetch_templates.main(fetch_args)

    if parsed_args.command == "create":
        create_args = ["--input", parsed_args.input]
        if parsed_args.title:
            create_args.extend(["--title", parsed_args.title])
        if parsed_args.notes:
            create_args.extend(["--notes", parsed_args.notes])
        if parsed_args.folder:
            create_args.extend(["--folder", parsed_args.folder])
        if parsed_args.validate_only:
            create_args.append("--validate-only")
        if parsed_args.auto_fix:
            create_args.append("--auto-fix")
        if parsed_args.verbose:
            create_args.append("--verbose")
        return create_routine.main(create_args)

    if parsed_args.command == "validate":
        create_args = [
            "--input",
            parsed_args.input,
            "--validate-only",
        ]
        if parsed_args.verbose:
            create_args.append("--verbose")
        return create_routine.main(create_args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
