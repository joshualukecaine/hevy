"""Pytest configuration and fixtures."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from hevy.models import Exercise, ExerciseSet, ExerciseTemplate, WorkoutDay, WorkoutProgram


@pytest.fixture
def sample_exercise_template() -> ExerciseTemplate:
    """Create a sample exercise template."""
    return ExerciseTemplate(
        id="392887AA",
        title="Push Up",
        primary_muscle_group="chest",
        secondary_muscle_groups=["triceps", "shoulders"],
        equipment="bodyweight",
        is_custom=False,
    )


@pytest.fixture
def sample_templates() -> list[ExerciseTemplate]:
    """Create a list of sample exercise templates."""
    return [
        ExerciseTemplate(
            id="392887AA",
            title="Push Up",
            primary_muscle_group="chest",
            equipment="bodyweight",
        ),
        ExerciseTemplate(
            id="ABC12345",
            title="Pull Up",
            primary_muscle_group="back",
            equipment="bodyweight",
        ),
        ExerciseTemplate(
            id="DEF67890",
            title="Squat",
            primary_muscle_group="quadriceps",
            equipment="bodyweight",
        ),
        ExerciseTemplate(
            id="C6C9B8A0",
            title="Plank",
            primary_muscle_group="core",
            equipment="bodyweight",
        ),
    ]


@pytest.fixture
def sample_exercise() -> Exercise:
    """Create a sample exercise."""
    return Exercise(
        name="Push Up",
        exercise_template_id="392887AA",
        sets=[
            ExerciseSet(type="normal", reps=10),
            ExerciseSet(type="normal", reps=10),
            ExerciseSet(type="normal", reps=10),
        ],
        rest_seconds=60,
        notes="Focus on form",
    )


@pytest.fixture
def sample_workout_day() -> WorkoutDay:
    """Create a sample workout day."""
    return WorkoutDay(
        day=1,
        name="Upper Body Day",
        description="Focus on chest and back",
        duration_minutes=45,
        exercises=[
            Exercise(
                name="Push Up",
                exercise_template_id="392887AA",
                sets=[ExerciseSet(reps=10) for _ in range(3)],
                rest_seconds=60,
            ),
            Exercise(
                name="Pull Up",
                exercise_template_id="ABC12345",
                sets=[ExerciseSet(reps=8) for _ in range(3)],
                rest_seconds=90,
            ),
        ],
    )


@pytest.fixture
def sample_program() -> WorkoutProgram:
    """Create a sample workout program."""
    return WorkoutProgram(
        program_name="Test Program",
        program_description="A test workout program",
        days=[
            WorkoutDay(
                day=1,
                name="Day 1",
                exercises=[
                    Exercise(
                        name="Push Up",
                        exercise_template_id="392887AA",
                        sets=[ExerciseSet(reps=10) for _ in range(3)],
                    ),
                ],
            ),
        ],
    )


@pytest.fixture
def sample_program_json() -> dict[str, Any]:
    """Create sample program JSON data."""
    return {
        "program_name": "Test Program",
        "program_description": "A test workout program",
        "days": [
            {
                "day": 1,
                "name": "Upper Body",
                "description": "Chest and back focus",
                "duration_minutes": 45,
                "exercises": [
                    {
                        "name": "Push Up",
                        "exercise_template_id": "392887AA",
                        "sets": 3,
                        "reps": 10,
                        "rest_seconds": 60,
                        "notes": "Focus on form",
                    },
                ],
            },
        ],
    }


@pytest.fixture
def sample_superset_json() -> dict[str, Any]:
    """Create sample program JSON with a superset."""
    return {
        "program_name": "Superset Program",
        "days": [
            {
                "day": 1,
                "name": "Push Pull",
                "exercises": [
                    {
                        "superset": {
                            "name": "Chest & Back",
                            "exercises": [
                                {
                                    "name": "Push Up",
                                    "exercise_template_id": "392887AA",
                                    "sets": 3,
                                    "reps": 10,
                                },
                                {
                                    "name": "Pull Up",
                                    "exercise_template_id": "ABC12345",
                                    "sets": 3,
                                    "reps": 8,
                                },
                            ],
                        },
                    },
                ],
            },
        ],
    }


@pytest.fixture
def sample_circuit_json() -> dict[str, Any]:
    """Create sample program JSON with a circuit."""
    return {
        "program_name": "Circuit Program",
        "days": [
            {
                "day": 1,
                "name": "Full Body Circuit",
                "exercises": [
                    {
                        "circuit": {
                            "name": "Core Blast",
                            "rounds": 3,
                            "exercises": [
                                {
                                    "name": "Plank",
                                    "exercise_template_id": "C6C9B8A0",
                                    "reps": "30 seconds",
                                },
                                {
                                    "name": "Squat",
                                    "exercise_template_id": "DEF67890",
                                    "reps": 15,
                                },
                            ],
                        },
                    },
                ],
            },
        ],
    }


@pytest.fixture
def mock_hevy_client() -> MagicMock:
    """Create a mock Hevy API client."""
    client = MagicMock()
    client.create_routine.return_value = "routine-123"
    client.create_routine_folder.return_value = "folder-456"
    return client


@pytest.fixture
def tmp_cache_file(tmp_path: Path) -> Path:
    """Create a temporary cache file."""
    cache_file = tmp_path / "templates.json"
    data = {
        "metadata": {
            "last_updated": "2024-01-01T00:00:00",
            "count": 2,
        },
        "templates": [
            {
                "id": "392887AA",
                "title": "Push Up",
                "primary_muscle_group": "chest",
                "equipment": "bodyweight",
            },
            {
                "id": "ABC12345",
                "title": "Pull Up",
                "primary_muscle_group": "back",
                "equipment": "bodyweight",
            },
        ],
    }
    cache_file.write_text(json.dumps(data))
    return cache_file
