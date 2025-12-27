#!/usr/bin/env python3
"""Fetch exercise templates from the Hevy API.

Downloads all available exercise templates and caches them locally
for offline use and faster lookups.

Usage:
    hevy-fetch [--force] [--output PATH]
"""

import argparse
import logging
import sys

from hevy.api import HevyAPIError, HevyClient
from hevy.cli.logging_config import setup_logging
from hevy.core import TemplateCache

logger = logging.getLogger(__name__)

DEFAULT_CACHE_PATH = "./data/exercise_templates.json"


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Fetch exercise templates from the Hevy API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    hevy-fetch                          # Fetch if cache is stale (>30 days)
    hevy-fetch --force                  # Force refresh
    hevy-fetch --output ./templates.json  # Custom output path
        """,
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force update even if cache is recent",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=DEFAULT_CACHE_PATH,
        help=f"Output file path (default: {DEFAULT_CACHE_PATH})",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    return parser


def main(args: list[str] | None = None) -> int:
    """Main entry point for the fetch-templates command.

    Args:
        args: Command line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    setup_logging(verbose=parsed_args.verbose)

    cache = TemplateCache(parsed_args.output)

    # Check if update is needed
    if not cache.should_update(force=parsed_args.force):
        age = cache.get_age_days()
        print(f"Exercise templates are up to date ({age} days old).")
        print("Use --force to update anyway.")
        return 0

    try:
        # Create client and fetch templates
        client = HevyClient.from_env()

        print("Fetching exercise templates from Hevy API...")
        templates = client.get_all_exercise_templates()

        # Save to cache
        cache.save(templates)

        print(f"Successfully saved {len(templates)} exercise templates to {parsed_args.output}")
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
