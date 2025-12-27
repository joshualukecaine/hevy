"""Hevy API client implementation."""

import logging
import os
import time
from typing import Any

import requests
from dotenv import load_dotenv

from hevy.api.exceptions import (
    HevyAPIError,
    HevyAuthenticationError,
    HevyNotFoundError,
    HevyRateLimitError,
    HevyValidationError,
)
from hevy.models import ExerciseTemplate, Routine, RoutineFolder

logger = logging.getLogger(__name__)


class HevyClient:
    """Client for interacting with the Hevy API.

    Usage:
        # From environment variable
        client = HevyClient.from_env()

        # With explicit API key
        client = HevyClient(api_key="your-api-key")

        # Create a routine
        routine = Routine(title="My Workout", exercises=[...])
        routine_id = client.create_routine(routine)
    """

    BASE_URL = "https://api.hevyapp.com/v1"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0

    def __init__(self, api_key: str, timeout: int = DEFAULT_TIMEOUT):
        """Initialize the Hevy API client.

        Args:
            api_key: Your Hevy API key
            timeout: Request timeout in seconds
        """
        if not api_key:
            raise HevyAuthenticationError("API key cannot be empty")

        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "api-key": api_key,
            }
        )

    @classmethod
    def from_env(cls, env_file: str | None = None) -> "HevyClient":
        """Create a client from environment variables.

        Args:
            env_file: Path to .env file (optional)

        Returns:
            Configured HevyClient instance

        Raises:
            HevyAuthenticationError: If HEVY_API_KEY is not found
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        api_key = os.getenv("HEVY_API_KEY")
        if not api_key:
            raise HevyAuthenticationError(
                "HEVY_API_KEY not found in environment. "
                "Please set it in your .env file or environment variables."
            )
        return cls(api_key=api_key)

    def _request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        params: dict | None = None,
        retries: int = MAX_RETRIES,
    ) -> dict[str, Any]:
        """Make a request to the Hevy API with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters
            retries: Number of retries remaining

        Returns:
            Response data as dictionary

        Raises:
            HevyAPIError: On API errors
        """
        url = f"{self.BASE_URL}/{endpoint}"
        logger.debug("Making %s request to %s", method, url)

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout,
            )

            # Handle different status codes
            if response.status_code in (200, 201):
                return response.json()

            if response.status_code == 401:
                raise HevyAuthenticationError()

            if response.status_code == 404:
                raise HevyNotFoundError(f"Resource not found: {endpoint}")

            if response.status_code == 400:
                raise HevyValidationError(f"Invalid request: {response.text}")

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                if retries > 0:
                    logger.warning(
                        "Rate limited, waiting %d seconds before retry",
                        retry_after,
                    )
                    time.sleep(retry_after)
                    return self._request(method, endpoint, data, params, retries - 1)
                raise HevyRateLimitError(retry_after=retry_after)

            raise HevyAPIError(
                message=f"API error: {response.text}",
                status_code=response.status_code,
                response=response.text,
            )

        except requests.exceptions.Timeout:
            if retries > 0:
                logger.warning("Request timeout, retrying...")
                time.sleep(self.RETRY_DELAY)
                return self._request(method, endpoint, data, params, retries - 1)
            raise HevyAPIError("Request timeout") from None

        except requests.exceptions.ConnectionError as e:
            if retries > 0:
                logger.warning("Connection error, retrying...")
                time.sleep(self.RETRY_DELAY)
                return self._request(method, endpoint, data, params, retries - 1)
            raise HevyAPIError(f"Connection error: {e}") from e

    def get(self, endpoint: str, params: dict | None = None) -> dict[str, Any]:
        """Make a GET request."""
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: dict) -> dict[str, Any]:
        """Make a POST request."""
        return self._request("POST", endpoint, data=data)

    def put(self, endpoint: str, data: dict) -> dict[str, Any]:
        """Make a PUT request."""
        return self._request("PUT", endpoint, data=data)

    def delete(self, endpoint: str) -> dict[str, Any]:
        """Make a DELETE request."""
        return self._request("DELETE", endpoint)

    # --- Exercise Templates ---

    def get_exercise_templates(
        self,
        page: int = 1,
        per_page: int = 100,
    ) -> list[ExerciseTemplate]:
        """Fetch exercise templates from the API.

        Args:
            page: Page number (1-indexed)
            per_page: Number of templates per page (max 100)

        Returns:
            List of ExerciseTemplate objects
        """
        response = self.get(
            "exercise_templates",
            params={"page": page, "per_page": per_page},
        )
        templates = response.get("exercise_templates", [])
        return [ExerciseTemplate.from_api_response(t) for t in templates]

    def get_all_exercise_templates(self) -> list[ExerciseTemplate]:
        """Fetch all exercise templates from the API.

        Handles pagination automatically.

        Returns:
            List of all ExerciseTemplate objects
        """
        logger.info("Fetching all exercise templates...")
        all_templates: list[ExerciseTemplate] = []
        page = 1

        while True:
            response = self.get(
                "exercise_templates",
                params={"page": page, "per_page": 100},
            )
            templates = response.get("exercise_templates", [])
            all_templates.extend(ExerciseTemplate.from_api_response(t) for t in templates)

            page_count = response.get("page_count", page)
            if page >= page_count:
                break
            page += 1

        logger.info("Fetched %d exercise templates", len(all_templates))
        return all_templates

    def get_exercise_template(self, template_id: str) -> ExerciseTemplate:
        """Fetch a single exercise template by ID.

        Args:
            template_id: The template ID

        Returns:
            ExerciseTemplate object

        Raises:
            HevyNotFoundError: If template not found
        """
        response = self.get(f"exercise_templates/{template_id}")
        return ExerciseTemplate.from_api_response(response)

    # --- Routines ---

    def create_routine(self, routine: Routine) -> str:
        """Create a new routine.

        Args:
            routine: Routine object to create

        Returns:
            The created routine's ID
        """
        logger.info("Creating routine: %s", routine.title)
        response = self.post("routines", routine.to_api_format())
        # API may return {"routine": {...}} or {"routine": [{...}]}
        routine_data = response.get("routine", {})
        if isinstance(routine_data, list):
            routine_id = routine_data[0].get("id", "") if routine_data else ""
        else:
            routine_id = routine_data.get("id", "")
        routine_id = str(routine_id) if routine_id else ""
        logger.info("Created routine with ID: %s", routine_id)
        return routine_id

    def get_routines(
        self,
        page: int = 1,
        per_page: int = 20,
        folder_id: str | None = None,
    ) -> list[dict]:
        """Fetch routines from the API.

        Args:
            page: Page number
            per_page: Results per page
            folder_id: Filter by folder ID

        Returns:
            List of routine dictionaries
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if folder_id:
            params["folder_id"] = folder_id
        response = self.get("routines", params=params)
        return response.get("routines", [])

    def update_routine(self, routine_id: str, routine: Routine) -> dict:
        """Update an existing routine.

        Args:
            routine_id: ID of routine to update
            routine: Updated routine data

        Returns:
            Updated routine data
        """
        logger.info("Updating routine: %s", routine_id)
        return self.put(f"routines/{routine_id}", routine.to_api_format())

    # --- Routine Folders ---

    def create_routine_folder(self, title: str) -> str:
        """Create a new routine folder.

        Args:
            title: Folder title

        Returns:
            The created folder's ID
        """
        logger.info("Creating routine folder: %s", title)
        folder = RoutineFolder(title=title)
        response = self.post("routine_folders", folder.to_api_format())
        folder_id = response.get("routine_folder", {}).get("id", "")
        # API may return int, ensure we return string
        folder_id = str(folder_id) if folder_id else ""
        logger.info("Created folder with ID: %s", folder_id)
        return folder_id

    def get_routine_folders(
        self,
        page: int = 1,
        per_page: int = 20,
    ) -> list[dict]:
        """Fetch routine folders from the API."""
        response = self.get(
            "routine_folders",
            params={"page": page, "per_page": per_page},
        )
        return response.get("routine_folders", [])

    # --- Workouts ---

    def get_workouts(
        self,
        page: int = 1,
        per_page: int = 20,
    ) -> list[dict]:
        """Fetch workouts from the API."""
        response = self.get(
            "workouts",
            params={"page": page, "per_page": per_page},
        )
        return response.get("workouts", [])

    def get_workout_count(self) -> int:
        """Get total number of workouts."""
        response = self.get("workouts/count")
        return response.get("count", 0)
