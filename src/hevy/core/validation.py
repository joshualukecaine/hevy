"""Validation logic for exercises and routines."""

import logging
from dataclasses import dataclass, field

from hevy.models import Exercise, ExerciseTemplate, WorkoutProgram

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Represents a validation error for an exercise."""

    day_name: str
    day_index: int
    exercise_name: str
    exercise_index: int
    template_id: str
    reason: str
    alternatives: list[ExerciseTemplate] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of validating a workout program."""

    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    def add_error(self, error: ValidationError) -> None:
        self.errors.append(error)
        self.is_valid = False


def is_valid_hevy_id(template_id: str) -> bool:
    """Check if a template ID has a valid Hevy format.

    Accepts both formats:
    - 8 character hexadecimal (e.g., '3D0C7C75') - built-in exercises
    - UUID format (e.g., '13084c79-fd76-432e-b7d6-4ad3c67ddf81') - custom exercises
    """
    if not template_id:
        return False

    # Check for 8-character hex format (built-in exercises)
    if len(template_id) == 8:
        return all(c in "0123456789ABCDEFabcdef" for c in template_id)

    # Check for UUID format (custom exercises)
    if len(template_id) == 36 and template_id.count("-") == 4:
        parts = template_id.split("-")
        if (
            len(parts) == 5
            and len(parts[0]) == 8
            and len(parts[1]) == 4
            and len(parts[2]) == 4
            and len(parts[3]) == 4
            and len(parts[4]) == 12
        ):
            return all(c in "0123456789ABCDEFabcdef-" for c in template_id)

    return False


def find_alternatives(
    exercise: Exercise,
    templates: list[ExerciseTemplate],
    max_results: int = 30,
) -> list[ExerciseTemplate]:
    """Find alternative exercises based on muscle group and equipment.

    Args:
        exercise: The exercise to find alternatives for
        templates: List of all available templates
        max_results: Maximum number of alternatives to return

    Returns:
        List of matching ExerciseTemplate objects
    """
    # Try to match by category if available
    category = exercise.category.lower() if exercise.category else ""

    alternatives = []
    for template in templates:
        # Match by primary muscle group
        if (
            category
            and template.primary_muscle_group.lower() == category
            or exercise.name.lower() in template.title.lower()
        ):
            alternatives.append(template)

    return alternatives[:max_results]


def validate_exercise(
    exercise: Exercise,
    template_ids: set[str],
) -> str | None:
    """Validate a single exercise's template ID.

    Args:
        exercise: The exercise to validate
        template_ids: Set of valid template IDs

    Returns:
        Error message if invalid, None if valid
    """
    template_id = exercise.exercise_template_id

    if not is_valid_hevy_id(template_id):
        return f"Invalid ID format - must be 8 hex characters or UUID: {template_id}"

    if template_id not in template_ids:
        return f"Template ID not found in Hevy database: {template_id}"

    return None


def validate_program(
    program: WorkoutProgram,
    templates: list[ExerciseTemplate],
) -> ValidationResult:
    """Validate all exercises in a workout program.

    Args:
        program: The workout program to validate
        templates: List of valid exercise templates

    Returns:
        ValidationResult with any errors found
    """
    result = ValidationResult(is_valid=True)
    template_ids = {t.id for t in templates}

    for day_idx, day in enumerate(program.days):
        for ex_idx, exercise in enumerate(day.exercises):
            error_msg = validate_exercise(exercise, template_ids)

            if error_msg:
                alternatives = find_alternatives(exercise, templates)
                error = ValidationError(
                    day_name=day.name,
                    day_index=day_idx,
                    exercise_name=exercise.name,
                    exercise_index=ex_idx,
                    template_id=exercise.exercise_template_id,
                    reason=error_msg,
                    alternatives=alternatives,
                )
                result.add_error(error)
                logger.warning(
                    "Invalid exercise in %s: %s - %s",
                    day.name,
                    exercise.name,
                    error_msg,
                )

    if result.is_valid:
        logger.info("Program validation passed: all exercises are valid")
    else:
        logger.warning("Program validation failed: %d errors", result.error_count)

    return result
