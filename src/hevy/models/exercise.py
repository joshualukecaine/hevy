"""Exercise-related data models."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SetType(str, Enum):
    """Type of exercise set."""

    NORMAL = "normal"
    WARMUP = "warmup"
    DROP = "drop"
    FAILURE = "failure"


class ExerciseSet(BaseModel):
    """Represents a single set of an exercise."""

    type: SetType = SetType.NORMAL
    weight_kg: float | None = None
    reps: int | None = None
    distance_meters: float | None = None
    duration_seconds: int | None = None
    custom_metric: float | None = None
    rpe: float | None = Field(None, ge=1, le=10)

    def to_api_format(self) -> dict[str, Any]:
        """Convert to Hevy API format for routines.

        Note: RPE is only allowed in workouts, not routines.
        """
        return {
            "type": self.type.value,
            "weight_kg": self.weight_kg,
            "reps": self.reps,
            "distance_meters": self.distance_meters,
            "duration_seconds": self.duration_seconds,
            "custom_metric": self.custom_metric,
        }


class Exercise(BaseModel):
    """Represents an exercise in a routine or workout."""

    name: str
    exercise_template_id: str
    sets: list[ExerciseSet] = Field(default_factory=list)
    superset_id: int | None = None
    rest_seconds: int = 60
    notes: str = ""
    category: str = ""

    @field_validator("exercise_template_id")
    @classmethod
    def validate_template_id(cls, v: str) -> str:
        """Validate exercise template ID format."""
        if not v:
            raise ValueError("Exercise template ID cannot be empty")
        # 8-char hex (built-in) or UUID format (custom)
        if len(v) == 8:
            if not all(c in "0123456789ABCDEFabcdef" for c in v):
                raise ValueError(f"Invalid 8-char hex ID: {v}")
        elif len(v) == 36 and v.count("-") == 4:
            parts = v.split("-")
            if not (
                len(parts) == 5
                and len(parts[0]) == 8
                and len(parts[1]) == 4
                and len(parts[2]) == 4
                and len(parts[3]) == 4
                and len(parts[4]) == 12
            ):
                raise ValueError(f"Invalid UUID format: {v}")
        else:
            raise ValueError(f"Invalid template ID format: {v}")
        return v

    def to_api_format(self) -> dict[str, Any]:
        """Convert to Hevy API format."""
        return {
            "exercise_template_id": self.exercise_template_id,
            "superset_id": self.superset_id,
            "rest_seconds": self.rest_seconds,
            "notes": self.notes,
            "sets": [s.to_api_format() for s in self.sets],
        }

    @classmethod
    def from_json(
        cls,
        data: dict[str, Any],
        superset_id: int | None = None,
    ) -> "Exercise":
        """Create Exercise from JSON routine format.

        Supports both simple format (sets: 3, reps: 10) and detailed format.
        """
        sets = cls._parse_sets(data)
        return cls(
            name=data.get("name", ""),
            exercise_template_id=data.get("exercise_template_id", ""),
            sets=sets,
            superset_id=superset_id,
            rest_seconds=data.get("rest_seconds", 60),
            notes=data.get("notes", ""),
            category=data.get("category", ""),
        )

    @staticmethod
    def _parse_sets(data: dict[str, Any]) -> list["ExerciseSet"]:
        """Parse sets from JSON data."""
        # If detailed sets are provided, use them
        if "detailed_sets" in data:
            return [ExerciseSet(**s) for s in data["detailed_sets"]]

        # Otherwise, create sets from simple format
        num_sets = data.get("sets", 1)
        reps_value = data.get("reps", "")

        base_set = ExerciseSet()

        if isinstance(reps_value, str):
            duration = _parse_duration_to_seconds(reps_value)
            if duration:
                base_set = ExerciseSet(duration_seconds=duration)
            else:
                try:
                    base_set = ExerciseSet(reps=int(reps_value))
                except ValueError:
                    base_set = ExerciseSet(reps=1)
        elif isinstance(reps_value, int):
            base_set = ExerciseSet(reps=reps_value)

        return [base_set.model_copy() for _ in range(num_sets)]


class ExerciseTemplate(BaseModel):
    """Represents an exercise template from the Hevy API."""

    id: str
    title: str
    primary_muscle_group: str = ""
    secondary_muscle_groups: list[str] = Field(default_factory=list)
    equipment: str = ""
    is_custom: bool = False

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "ExerciseTemplate":
        """Create from Hevy API response."""
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            primary_muscle_group=data.get("primary_muscle_group", ""),
            secondary_muscle_groups=data.get("secondary_muscle_groups", []),
            equipment=data.get("equipment", ""),
            is_custom=data.get("is_custom", False),
        )


def _parse_duration_to_seconds(value: str) -> int | None:
    """Parse duration strings like '5 minutes' or '30 seconds' to seconds."""
    value_lower = value.lower()
    if "minute" in value_lower:
        try:
            return int(value.split()[0]) * 60
        except (ValueError, IndexError):
            return 60
    elif "second" in value_lower:
        try:
            return int(value.split()[0])
        except (ValueError, IndexError):
            return 30
    return None
