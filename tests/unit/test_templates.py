"""Tests for template cache."""

import json
from datetime import datetime, timedelta

from hevy.core.templates import TemplateCache
from hevy.models import ExerciseTemplate


class TestTemplateCache:
    """Tests for TemplateCache class."""

    def test_exists(self, tmp_cache_file):
        """Test exists() method."""
        cache = TemplateCache(tmp_cache_file)
        assert cache.exists() is True

        non_existent = TemplateCache("/nonexistent/path.json")
        assert non_existent.exists() is False

    def test_load(self, tmp_cache_file):
        """Test loading templates from cache."""
        cache = TemplateCache(tmp_cache_file)
        templates = cache.load()
        assert len(templates) == 2
        assert templates[0].id == "392887AA"
        assert templates[0].title == "Push Up"

    def test_save(self, tmp_path):
        """Test saving templates to cache."""
        cache_file = tmp_path / "new_cache.json"
        cache = TemplateCache(cache_file)

        templates = [
            ExerciseTemplate(id="11111111", title="Test Exercise"),
        ]
        cache.save(templates)

        assert cache_file.exists()
        data = json.loads(cache_file.read_text())
        assert "metadata" in data
        assert data["metadata"]["count"] == 1
        assert len(data["templates"]) == 1

    def test_should_update_no_file(self, tmp_path):
        """Test should_update when file doesn't exist."""
        cache = TemplateCache(tmp_path / "nonexistent.json")
        assert cache.should_update() is True

    def test_should_update_fresh_cache(self, tmp_path):
        """Test should_update with fresh cache."""
        cache_file = tmp_path / "fresh.json"
        data = {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "count": 1,
            },
            "templates": [],
        }
        cache_file.write_text(json.dumps(data))

        cache = TemplateCache(cache_file)
        assert cache.should_update() is False

    def test_should_update_stale_cache(self, tmp_path):
        """Test should_update with stale cache."""
        cache_file = tmp_path / "stale.json"
        old_date = datetime.now() - timedelta(days=31)
        data = {
            "metadata": {
                "last_updated": old_date.isoformat(),
                "count": 1,
            },
            "templates": [],
        }
        cache_file.write_text(json.dumps(data))

        cache = TemplateCache(cache_file)
        assert cache.should_update() is True

    def test_should_update_force(self, tmp_cache_file):
        """Test should_update with force=True."""
        cache = TemplateCache(tmp_cache_file)
        assert cache.should_update(force=True) is True

    def test_get_template_by_id(self, tmp_cache_file):
        """Test finding template by ID."""
        cache = TemplateCache(tmp_cache_file)
        template = cache.get_template_by_id("392887AA")
        assert template is not None
        assert template.title == "Push Up"

        not_found = cache.get_template_by_id("NOTFOUND")
        assert not_found is None

    def test_get_template_by_name(self, tmp_cache_file):
        """Test finding template by name."""
        cache = TemplateCache(tmp_cache_file)
        template = cache.get_template_by_name("Push Up")
        assert template is not None
        assert template.id == "392887AA"

        # Case insensitive
        template2 = cache.get_template_by_name("push up")
        assert template2 is not None

    def test_search_templates(self, tmp_cache_file):
        """Test searching templates."""
        cache = TemplateCache(tmp_cache_file)

        # Exact match
        results = cache.search_templates("Push Up")
        assert len(results) >= 1
        assert results[0].title == "Push Up"

        # Partial match
        results = cache.search_templates("Pull")
        assert len(results) >= 1
        assert any(t.title == "Pull Up" for t in results)

    def test_build_name_to_id_map(self, tmp_cache_file):
        """Test building name-to-ID mapping."""
        cache = TemplateCache(tmp_cache_file)
        mapping = cache.build_name_to_id_map()

        assert "push up" in mapping
        assert mapping["push up"] == "392887AA"

    def test_get_age_days(self, tmp_path):
        """Test getting cache age."""
        cache_file = tmp_path / "aged.json"
        old_date = datetime.now() - timedelta(days=5)
        data = {
            "metadata": {
                "last_updated": old_date.isoformat(),
                "count": 0,
            },
            "templates": [],
        }
        cache_file.write_text(json.dumps(data))

        cache = TemplateCache(cache_file)
        age = cache.get_age_days()
        assert age == 5

    def test_get_age_days_no_file(self, tmp_path):
        """Test age when file doesn't exist."""
        cache = TemplateCache(tmp_path / "nonexistent.json")
        assert cache.get_age_days() is None
