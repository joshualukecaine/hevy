#!/usr/bin/env python3
"""Delete routines and folders from Hevy.

Usage:
    hevy delete --routine ID [--routine ID ...]
    hevy delete --folder ID [--keep-routines]
"""

import argparse
import logging
import sys

from hevy.api import HevyAPIError, HevyClient
from hevy.cli.logging_config import setup_logging

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Delete routines and folders from Hevy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    hevy delete --routine abc123
    hevy delete --routine abc123 --routine def456
    hevy delete --folder xyz789
    hevy delete --folder xyz789 --keep-routines

Use 'hevy list' to find routine and folder IDs.
        """,
    )
    parser.add_argument(
        "--routine",
        "-r",
        action="append",
        dest="routines",
        metavar="ID",
        help="Routine ID to delete (can be specified multiple times)",
    )
    parser.add_argument(
        "--folder",
        "-f",
        metavar="ID",
        help="Folder ID to delete (deletes all routines in folder by default)",
    )
    parser.add_argument(
        "--keep-routines",
        action="store_true",
        help="When deleting a folder, keep the routines (just delete the folder)",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    return parser


def main(args: list[str] | None = None) -> int:
    """Main entry point for the delete command.

    Args:
        args: Command line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    setup_logging(verbose=parsed_args.verbose)

    if not parsed_args.routines and not parsed_args.folder:
        parser.error("Must specify --routine or --folder to delete")

    try:
        client = HevyClient.from_env()

        # Confirm deletion
        if not parsed_args.yes:
            items = []
            if parsed_args.routines:
                items.append(f"{len(parsed_args.routines)} routine(s)")
            if parsed_args.folder:
                if parsed_args.keep_routines:
                    items.append("1 folder (keeping routines)")
                else:
                    items.append("1 folder and all its routines")

            print(f"About to delete: {', '.join(items)}")
            confirm = input("Are you sure? [y/N] ").strip().lower()
            if confirm != "y":
                print("Cancelled.")
                return 0

        # Delete routines
        if parsed_args.routines:
            for routine_id in parsed_args.routines:
                print(f"Deleting routine {routine_id}...")
                client.delete_routine(routine_id)
                print(f"  Deleted routine {routine_id}")

        # Delete folder
        if parsed_args.folder:
            delete_routines = not parsed_args.keep_routines
            if delete_routines:
                print(f"Deleting folder {parsed_args.folder} and all routines...")
            else:
                print(f"Deleting folder {parsed_args.folder} (keeping routines)...")

            client.delete_routine_folder(
                parsed_args.folder,
                delete_routines=delete_routines,
            )
            print(f"  Deleted folder {parsed_args.folder}")

        print("\nDone!")
        return 0

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
