"""Tests for validation logic."""

from hevy.core.validation import (
    find_alternatives,
    is_valid_hevy_id,
    validate_exercise,
    validate_program,
)
from hevy.models import Exercise, ExerciseSet, WorkoutDay, WorkoutProgram


class TestIsValidHevyId:
    """Tests for is_valid_hevy_id function."""

    def test_valid_hex_id(self):
        """Test valid 8-char hex IDs."""
        assert is_valid_hevy_id("392887AA") is True
        assert is_valid_hevy_id("3D0C7C75") is True
        assert is_valid_hevy_id("abcdef12") is True

    def test_valid_uuid_id(self):
        """Test valid UUID format IDs."""
        assert is_valid_hevy_id("13084c79-fd76-432e-b7d6-4ad3c67ddf81") is True
        assert is_valid_hevy_id("AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE") is True

    def test_invalid_empty(self):
        """Test empty string is invalid."""
        assert is_valid_hevy_id("") is False
        assert is_valid_hevy_id(None) is False  # type: ignore

    def test_invalid_length(self):
        """Test wrong length is invalid."""
        assert is_valid_hevy_id("12345") is False
        assert is_valid_hevy_id("123456789") is False

    def test_invalid_characters(self):
        """Test non-hex characters are invalid."""
        assert is_valid_hevy_id("GHIJKLMN") is False
        assert is_valid_hevy_id("392887A!") is False

    def test_invalid_uuid_format(self):
        """Test malformed UUID is invalid."""
        assert is_valid_hevy_id("13084c79-fd76-432e-b7d6") is False
        assert is_valid_hevy_id("13084c79fd76432eb7d64ad3c67ddf81") is False


class TestValidateExercise:
    """Tests for validate_exercise function."""

    def test_valid_exercise(self, sample_templates):
        """Test valid exercise passes validation."""
        exercise = Exercise(
            name="Push Up",
            exercise_template_id="392887AA",
            sets=[ExerciseSet(reps=10)],
        )
        template_ids = {t.id for t in sample_templates}
        error = validate_exercise(exercise, template_ids)
        assert error is None

    def test_invalid_id_format(self, sample_templates):
        """Test invalid ID format is caught."""
        # Create a mock exercise since Pydantic won't allow invalid ID
        from unittest.mock import MagicMock

        mock_exercise = MagicMock()
        mock_exercise.exercise_template_id = "INVALID!"
        template_ids = {t.id for t in sample_templates}
        error = validate_exercise(mock_exercise, template_ids)
        assert error is not None
        assert "Invalid ID format" in error

    def test_unknown_template_id(self, sample_templates):
        """Test unknown template ID is caught."""
        exercise = Exercise(
            name="Unknown",
            exercise_template_id="FFFFFFFF",
            sets=[ExerciseSet(reps=10)],
        )
        template_ids = {t.id for t in sample_templates}
        error = validate_exercise(exercise, template_ids)
        assert error is not None
        assert "not found" in error


class TestFindAlternatives:
    """Tests for find_alternatives function."""

    def test_find_by_category(self, sample_templates):
        """Test finding alternatives by category."""
        exercise = Exercise(
            name="Chest Press",
            exercise_template_id="FFFFFFFF",
            category="chest",
            sets=[ExerciseSet(reps=10)],
        )
        alternatives = find_alternatives(exercise, sample_templates)
        assert len(alternatives) > 0
        assert any(a.title == "Push Up" for a in alternatives)

    def test_find_by_name(self, sample_templates):
        """Test finding alternatives by name similarity."""
        exercise = Exercise(
            name="Pull",
            exercise_template_id="FFFFFFFF",
            sets=[ExerciseSet(reps=10)],
        )
        alternatives = find_alternatives(exercise, sample_templates)
        assert any(a.title == "Pull Up" for a in alternatives)

    def test_max_results(self, sample_templates):
        """Test max_results limit."""
        exercise = Exercise(
            name="Exercise",
            exercise_template_id="FFFFFFFF",
            category="back",
            sets=[ExerciseSet(reps=10)],
        )
        alternatives = find_alternatives(exercise, sample_templates, max_results=1)
        assert len(alternatives) <= 1


class TestValidateProgram:
    """Tests for validate_program function."""

    def test_valid_program(self, sample_templates):
        """Test valid program passes validation."""
        program = WorkoutProgram(
            program_name="Test",
            days=[
                WorkoutDay(
                    day=1,
                    name="Day 1",
                    exercises=[
                        Exercise(
                            name="Push Up",
                            exercise_template_id="392887AA",
                            sets=[ExerciseSet(reps=10)],
                        )
                    ],
                )
            ],
        )
        result = validate_program(program, sample_templates)
        assert result.is_valid is True
        assert result.error_count == 0

    def test_invalid_program(self, sample_templates):
        """Test invalid program fails validation."""
        program = WorkoutProgram(
            program_name="Test",
            days=[
                WorkoutDay(
                    day=1,
                    name="Day 1",
                    exercises=[
                        Exercise(
                            name="Bad Exercise",
                            exercise_template_id="FFFFFFFF",
                            sets=[ExerciseSet(reps=10)],
                        )
                    ],
                )
            ],
        )
        result = validate_program(program, sample_templates)
        assert result.is_valid is False
        assert result.error_count == 1
        assert result.errors[0].exercise_name == "Bad Exercise"

    def test_multiple_errors(self, sample_templates):
        """Test multiple errors are collected."""
        program = WorkoutProgram(
            program_name="Test",
            days=[
                WorkoutDay(
                    day=1,
                    name="Day 1",
                    exercises=[
                        Exercise(
                            name="Bad 1",
                            exercise_template_id="FFFFFFFF",
                            sets=[ExerciseSet(reps=10)],
                        ),
                        Exercise(
                            name="Bad 2",
                            exercise_template_id="EEEEEEEE",
                            sets=[ExerciseSet(reps=10)],
                        ),
                    ],
                )
            ],
        )
        result = validate_program(program, sample_templates)
        assert result.error_count == 2
