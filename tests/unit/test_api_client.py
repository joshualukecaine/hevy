"""Tests for the API client."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from hevy.api import (
    HevyAuthenticationError,
    HevyClient,
    HevyNotFoundError,
)
from hevy.models import Exercise, ExerciseSet, Routine


class TestHevyClientInit:
    """Tests for HevyClient initialization."""

    def test_init_with_api_key(self):
        """Test client initialization with API key."""
        client = HevyClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert "api-key" in client.session.headers

    def test_init_empty_api_key_raises(self):
        """Test that empty API key raises error."""
        with pytest.raises(HevyAuthenticationError):
            HevyClient(api_key="")

    @patch.dict("os.environ", {"HEVY_API_KEY": "env-test-key"})
    def test_from_env(self):
        """Test client creation from environment."""
        client = HevyClient.from_env()
        assert client.api_key == "env-test-key"

    def test_from_env_missing_key_raises(self, monkeypatch):
        """Test missing env key raises error."""
        monkeypatch.delenv("HEVY_API_KEY", raising=False)
        # Patch load_dotenv to do nothing (prevent loading .env file)
        with patch("hevy.api.client.load_dotenv"), pytest.raises(HevyAuthenticationError):
            HevyClient.from_env()


class TestHevyClientRequests:
    """Tests for HevyClient request methods."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return HevyClient(api_key="test-key")

    @pytest.fixture
    def mock_response(self):
        """Create a mock response."""
        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = {"data": "test"}
        return mock

    def test_get_success(self, client, mock_response):
        """Test successful GET request."""
        with patch.object(client.session, "request", return_value=mock_response):
            result = client.get("test-endpoint")
            assert result == {"data": "test"}

    def test_post_success(self, client, mock_response):
        """Test successful POST request."""
        mock_response.status_code = 201
        with patch.object(client.session, "request", return_value=mock_response):
            result = client.post("test-endpoint", {"key": "value"})
            assert result == {"data": "test"}

    def test_401_raises_auth_error(self, client):
        """Test 401 response raises authentication error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        with (
            patch.object(client.session, "request", return_value=mock_response),
            pytest.raises(HevyAuthenticationError),
        ):
            client.get("test-endpoint")

    def test_404_raises_not_found(self, client):
        """Test 404 response raises not found error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        with (
            patch.object(client.session, "request", return_value=mock_response),
            pytest.raises(HevyNotFoundError),
        ):
            client.get("test-endpoint")

    def test_rate_limit_with_retry(self, client):
        """Test rate limit triggers retry."""
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "1"}

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"success": True}

        with (
            patch.object(
                client.session,
                "request",
                side_effect=[rate_limit_response, success_response],
            ),
            patch("time.sleep"),
        ):
            result = client.get("test-endpoint")
            assert result == {"success": True}

    def test_timeout_with_retry(self, client):
        """Test timeout triggers retry."""
        with (
            patch.object(
                client.session,
                "request",
                side_effect=[
                    requests.exceptions.Timeout(),
                    MagicMock(status_code=200, json=lambda: {"success": True}),
                ],
            ),
            patch("time.sleep"),
        ):
            result = client.get("test-endpoint")
            assert result == {"success": True}


class TestHevyClientExerciseTemplates:
    """Tests for exercise template methods."""

    @pytest.fixture
    def client(self):
        return HevyClient(api_key="test-key")

    def test_get_exercise_templates(self, client):
        """Test fetching exercise templates."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "exercise_templates": [
                {"id": "TEST1234", "title": "Test Exercise"},
            ],
            "page_count": 1,
        }

        with patch.object(client.session, "request", return_value=mock_response):
            templates = client.get_exercise_templates()
            assert len(templates) == 1
            assert templates[0].id == "TEST1234"

    def test_get_all_exercise_templates(self, client):
        """Test fetching all templates with pagination."""
        page1 = MagicMock()
        page1.status_code = 200
        page1.json.return_value = {
            "exercise_templates": [{"id": "TEST1111", "title": "Ex 1"}],
            "page_count": 2,
        }

        page2 = MagicMock()
        page2.status_code = 200
        page2.json.return_value = {
            "exercise_templates": [{"id": "TEST2222", "title": "Ex 2"}],
            "page_count": 2,
        }

        with patch.object(client.session, "request", side_effect=[page1, page2]):
            templates = client.get_all_exercise_templates()
            assert len(templates) == 2


class TestHevyClientRoutines:
    """Tests for routine methods."""

    @pytest.fixture
    def client(self):
        return HevyClient(api_key="test-key")

    def test_create_routine(self, client):
        """Test creating a routine."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"routine": {"id": "routine-123"}}

        routine = Routine(
            title="Test Routine",
            exercises=[
                Exercise(
                    name="Push Up",
                    exercise_template_id="392887AA",
                    sets=[ExerciseSet(reps=10)],
                )
            ],
        )

        with patch.object(client.session, "request", return_value=mock_response):
            routine_id = client.create_routine(routine)
            assert routine_id == "routine-123"

    def test_create_routine_folder(self, client):
        """Test creating a routine folder."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"routine_folder": {"id": "folder-456"}}

        with patch.object(client.session, "request", return_value=mock_response):
            folder_id = client.create_routine_folder("My Folder")
            assert folder_id == "folder-456"
