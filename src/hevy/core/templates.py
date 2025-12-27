"""Exercise template caching and management."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from hevy.models import ExerciseTemplate

logger = logging.getLogger(__name__)


class TemplateCache:
    """Manages local caching of exercise templates.

    Templates are cached to avoid repeated API calls. The cache
    includes metadata for staleness detection.

    Usage:
        cache = TemplateCache("./data/exercise_templates.json")

        # Check if update is needed
        if cache.should_update(max_age_days=30):
            templates = client.get_all_exercise_templates()
            cache.save(templates)

        # Load cached templates
        templates = cache.load()
    """

    DEFAULT_MAX_AGE_DAYS = 30

    def __init__(self, cache_path: str | Path):
        """Initialize the template cache.

        Args:
            cache_path: Path to the cache file
        """
        self.cache_path = Path(cache_path)

    def exists(self) -> bool:
        """Check if the cache file exists."""
        return self.cache_path.exists()

    def load(self) -> list[ExerciseTemplate]:
        """Load templates from the cache file.

        Returns:
            List of ExerciseTemplate objects

        Raises:
            FileNotFoundError: If cache file doesn't exist
            json.JSONDecodeError: If cache file is invalid
        """
        logger.debug("Loading templates from cache: %s", self.cache_path)
        with open(self.cache_path, encoding="utf-8") as f:
            data = json.load(f)

        templates = data.get("templates", [])
        return [ExerciseTemplate.from_api_response(t) for t in templates]

    def load_raw(self) -> list[dict[str, Any]]:
        """Load raw template data from the cache file.

        Returns:
            List of template dictionaries
        """
        with open(self.cache_path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("templates", [])

    def save(self, templates: list[ExerciseTemplate]) -> None:
        """Save templates to the cache file.

        Args:
            templates: List of ExerciseTemplate objects to cache
        """
        logger.info("Saving %d templates to cache: %s", len(templates), self.cache_path)

        # Ensure directory exists
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "count": len(templates),
            },
            "templates": [self._template_to_dict(t) for t in templates],
        }

        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info("Cache saved successfully")

    def should_update(
        self,
        max_age_days: int = DEFAULT_MAX_AGE_DAYS,
        force: bool = False,
    ) -> bool:
        """Check if the cache should be updated.

        Args:
            max_age_days: Maximum age in days before update is needed
            force: If True, always return True

        Returns:
            True if cache should be updated
        """
        if force:
            return True

        if not self.exists():
            logger.info("Cache file does not exist, update needed")
            return True

        try:
            with open(self.cache_path, encoding="utf-8") as f:
                data = json.load(f)

            metadata = data.get("metadata", {})
            last_updated_str = metadata.get("last_updated")

            if not last_updated_str:
                logger.info("No last_updated in cache, update needed")
                return True

            last_updated = datetime.fromisoformat(last_updated_str)
            age_days = (datetime.now() - last_updated).days

            if age_days >= max_age_days:
                logger.info(
                    "Cache is %d days old (max: %d), update needed",
                    age_days,
                    max_age_days,
                )
                return True

            logger.info("Cache is %d days old, no update needed", age_days)
            return False

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Error reading cache metadata: %s", e)
            return True

    def get_age_days(self) -> int | None:
        """Get the age of the cache in days.

        Returns:
            Age in days, or None if cache doesn't exist or is invalid
        """
        if not self.exists():
            return None

        try:
            with open(self.cache_path, encoding="utf-8") as f:
                data = json.load(f)

            last_updated_str = data.get("metadata", {}).get("last_updated")
            if not last_updated_str:
                return None

            last_updated = datetime.fromisoformat(last_updated_str)
            return (datetime.now() - last_updated).days

        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def get_template_by_id(self, template_id: str) -> ExerciseTemplate | None:
        """Get a template by its ID.

        Args:
            template_id: The template ID to search for

        Returns:
            ExerciseTemplate if found, None otherwise
        """
        templates = self.load()
        for template in templates:
            if template.id == template_id:
                return template
        return None

    def get_template_by_name(self, name: str) -> ExerciseTemplate | None:
        """Get a template by its name (case-insensitive).

        Args:
            name: The template name to search for

        Returns:
            ExerciseTemplate if found, None otherwise
        """
        templates = self.load()
        name_lower = name.lower()
        for template in templates:
            if template.title.lower() == name_lower:
                return template
        return None

    def search_templates(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[ExerciseTemplate]:
        """Search templates by name.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of matching templates
        """
        templates = self.load()
        query_lower = query.lower()

        # Exact matches first, then partial matches
        exact = []
        partial = []

        for template in templates:
            title_lower = template.title.lower()
            if title_lower == query_lower:
                exact.append(template)
            elif query_lower in title_lower:
                partial.append(template)

        return (exact + partial)[:max_results]

    def build_name_to_id_map(self) -> dict[str, str]:
        """Build a mapping of lowercase names to template IDs.

        Returns:
            Dictionary mapping lowercase names to IDs
        """
        templates = self.load()
        return {t.title.lower(): t.id for t in templates}

    @staticmethod
    def _template_to_dict(template: ExerciseTemplate) -> dict[str, Any]:
        """Convert an ExerciseTemplate to a dictionary for JSON serialization."""
        return {
            "id": template.id,
            "title": template.title,
            "primary_muscle_group": template.primary_muscle_group,
            "secondary_muscle_groups": template.secondary_muscle_groups,
            "equipment": template.equipment,
            "is_custom": template.is_custom,
        }
