#!/usr/bin/env python3
"""List routines and folders from Hevy.

Usage:
    hevy list [--folders] [--routines] [--folder-id ID]
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
        description="List routines and folders from Hevy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--folders",
        action="store_true",
        help="List folders only",
    )
    parser.add_argument(
        "--routines",
        action="store_true",
        help="List routines only",
    )
    parser.add_argument(
        "--folder-id",
        help="Filter routines by folder ID",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    return parser


def main(args: list[str] | None = None) -> int:
    """Main entry point for the list command.

    Args:
        args: Command line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    setup_logging(verbose=parsed_args.verbose)

    try:
        client = HevyClient.from_env()

        # Default: show both folders and routines
        show_folders = parsed_args.folders or not parsed_args.routines
        show_routines = parsed_args.routines or not parsed_args.folders

        if show_folders and not parsed_args.folder_id:
            folders = client.get_routine_folders()
            if folders:
                print("\nFolders:")
                print("-" * 60)
                for folder in folders:
                    folder_id = folder.get("id", "")
                    title = folder.get("title", "Untitled")
                    print(f"  {folder_id}  {title}")
            else:
                print("\nNo folders found.")

        if show_routines:
            routines = client.get_routines(folder_id=parsed_args.folder_id)
            if routines:
                print("\nRoutines:")
                print("-" * 60)
                for routine in routines:
                    routine_id = routine.get("id", "")
                    title = routine.get("title", "Untitled")
                    folder_id = routine.get("folder_id", "")
                    folder_info = f" (folder: {folder_id})" if folder_id else ""
                    print(f"  {routine_id}  {title}{folder_info}")
            else:
                if parsed_args.folder_id:
                    print(f"\nNo routines found in folder {parsed_args.folder_id}.")
                else:
                    print("\nNo routines found.")

        print()
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
