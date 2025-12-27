"""Tests for data models."""

import pytest
from pydantic import ValidationError

from hevy.models import (
    Exercise,
    ExerciseSet,
    Routine,
    SetType,
    Superset,
    WorkoutDay,
    WorkoutProgram,
)


class TestExerciseSet:
    """Tests for ExerciseSet model."""

    def test_default_set(self):
        """Test default set creation."""
        s = ExerciseSet()
        assert s.type == SetType.NORMAL
        assert s.reps is None
        assert s.weight_kg is None

    def test_set_with_reps(self):
        """Test set with reps."""
        s = ExerciseSet(reps=10, weight_kg=50.0)
        assert s.reps == 10
        assert s.weight_kg == 50.0

    def test_set_with_duration(self):
        """Test set with duration."""
        s = ExerciseSet(duration_seconds=30)
        assert s.duration_seconds == 30
        assert s.reps is None

    def test_to_api_format(self):
        """Test API format conversion."""
        s = ExerciseSet(type=SetType.WARMUP, reps=5, weight_kg=20.0)
        api = s.to_api_format()
        assert api["type"] == "warmup"
        assert api["reps"] == 5
        assert api["weight_kg"] == 20.0

    def test_rpe_validation(self):
        """Test RPE must be between 1 and 10."""
        with pytest.raises(ValidationError):
            ExerciseSet(rpe=11)

        s = ExerciseSet(rpe=8.5)
        assert s.rpe == 8.5


class TestExercise:
    """Tests for Exercise model."""

    def test_valid_hex_id(self):
        """Test valid 8-char hex ID."""
        e = Exercise(name="Test", exercise_template_id="392887AA")
        assert e.exercise_template_id == "392887AA"

    def test_valid_uuid_id(self):
        """Test valid UUID format ID."""
        uuid_id = "13084c79-fd76-432e-b7d6-4ad3c67ddf81"
        e = Exercise(name="Test", exercise_template_id=uuid_id)
        assert e.exercise_template_id == uuid_id

    def test_invalid_id_format(self):
        """Test invalid ID format raises error."""
        with pytest.raises(ValidationError):
            Exercise(name="Test", exercise_template_id="invalid")

    def test_empty_id_raises_error(self):
        """Test empty ID raises error."""
        with pytest.raises(ValidationError):
            Exercise(name="Test", exercise_template_id="")

    def test_from_json_simple(self):
        """Test creating exercise from simple JSON format."""
        data = {
            "name": "Push Up",
            "exercise_template_id": "392887AA",
            "sets": 3,
            "reps": 10,
            "rest_seconds": 60,
        }
        e = Exercise.from_json(data)
        assert e.name == "Push Up"
        assert len(e.sets) == 3
        assert all(s.reps == 10 for s in e.sets)

    def test_from_json_with_duration(self):
        """Test creating exercise with duration reps."""
        data = {
            "name": "Plank",
            "exercise_template_id": "C6C9B8A0",
            "sets": 3,
            "reps": "30 seconds",
        }
        e = Exercise.from_json(data)
        assert len(e.sets) == 3
        assert all(s.duration_seconds == 30 for s in e.sets)

    def test_from_json_with_minutes(self):
        """Test creating exercise with minutes duration."""
        data = {
            "name": "Warm Up",
            "exercise_template_id": "79EF4E4F",
            "sets": 1,
            "reps": "5 minutes",
        }
        e = Exercise.from_json(data)
        assert e.sets[0].duration_seconds == 300

    def test_to_api_format(self):
        """Test API format conversion."""
        e = Exercise(
            name="Push Up",
            exercise_template_id="392887AA",
            sets=[ExerciseSet(reps=10)],
            rest_seconds=60,
            notes="Focus on form",
        )
        api = e.to_api_format()
        assert api["exercise_template_id"] == "392887AA"
        assert api["rest_seconds"] == 60
        assert api["notes"] == "Focus on form"
        assert len(api["sets"]) == 1


class TestSuperset:
    """Tests for Superset model."""

    def test_is_superset(self):
        """Test superset detection (2 exercises)."""
        s = Superset(exercises=[{}, {}])
        assert s.is_superset()
        assert not s.is_triset()
        assert not s.is_giant_set()

    def test_is_triset(self):
        """Test tri-set detection (3 exercises)."""
        s = Superset(exercises=[{}, {}, {}])
        assert not s.is_superset()
        assert s.is_triset()

    def test_is_giant_set(self):
        """Test giant set detection (4+ exercises)."""
        s = Superset(exercises=[{}, {}, {}, {}])
        assert s.is_giant_set()

    def test_expand_exercises(self):
        """Test expanding superset to individual exercises."""
        s = Superset(
            exercises=[
                {"name": "A", "exercise_template_id": "11111111"},
                {"name": "B", "exercise_template_id": "22222222"},
            ]
        )
        expanded = s.expand_exercises(superset_id=1)
        assert len(expanded) == 2
        assert all(ex["superset_id"] == 1 for ex in expanded)

    def test_circuit_rounds(self):
        """Test circuit with multiple rounds."""
        c = Superset(
            exercises=[
                {"name": "A", "sets": 1, "exercise_template_id": "11111111"},
                {"name": "B", "sets": 1, "exercise_template_id": "22222222"},
            ],
            rounds=3,
        )
        expanded = c.expand_exercises(superset_id=1)
        assert all(ex["sets"] == 3 for ex in expanded)


class TestWorkoutDay:
    """Tests for WorkoutDay model."""

    def test_from_json_regular_exercises(self, sample_program_json):
        """Test parsing regular exercises."""
        day_data = sample_program_json["days"][0]
        day = WorkoutDay.from_json(day_data)
        assert day.name == "Upper Body"
        assert len(day.exercises) == 1
        assert day.exercises[0].superset_id is None

    def test_from_json_with_superset(self, sample_superset_json):
        """Test parsing superset exercises."""
        day_data = sample_superset_json["days"][0]
        day = WorkoutDay.from_json(day_data)
        assert len(day.exercises) == 2
        assert day.exercises[0].superset_id == 1
        assert day.exercises[1].superset_id == 1

    def test_from_json_with_circuit(self, sample_circuit_json):
        """Test parsing circuit exercises."""
        day_data = sample_circuit_json["days"][0]
        day = WorkoutDay.from_json(day_data)
        assert len(day.exercises) == 2
        assert day.exercises[0].superset_id == 1
        # Circuit with 3 rounds should have 3 sets
        assert len(day.exercises[1].sets) == 3


class TestWorkoutProgram:
    """Tests for WorkoutProgram model."""

    def test_from_json(self, sample_program_json):
        """Test creating program from JSON."""
        program = WorkoutProgram.from_json(sample_program_json)
        assert program.program_name == "Test Program"
        assert len(program.days) == 1

    def test_get_all_template_ids(self, sample_program):
        """Test getting all template IDs."""
        ids = sample_program.get_all_template_ids()
        assert "392887AA" in ids


class TestRoutine:
    """Tests for Routine model."""

    def test_from_workout_day(self, sample_workout_day):
        """Test creating routine from workout day."""
        routine = Routine.from_workout_day(
            day=sample_workout_day,
            base_title="Week 1",
            notes="Test notes",
            folder_id="folder-123",
        )
        assert routine.title == "Week 1 - Upper Body Day"
        assert routine.folder_id == "folder-123"
        assert len(routine.exercises) == 2

    def test_to_api_format(self, sample_workout_day):
        """Test API format conversion."""
        routine = Routine.from_workout_day(sample_workout_day)
        api = routine.to_api_format()
        assert "routine" in api
        assert api["routine"]["title"] == "Upper Body Day"
        assert len(api["routine"]["exercises"]) == 2
