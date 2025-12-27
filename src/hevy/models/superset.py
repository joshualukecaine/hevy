"""Superset and circuit models."""

from typing import Any

from pydantic import BaseModel, Field


class Superset(BaseModel):
    """Represents a superset or circuit of exercises.

    A superset groups multiple exercises that are performed back-to-back
    with minimal rest between them. In Hevy, exercises with the same
    superset_id are grouped together.

    Types of groupings supported:
    - Superset (2 exercises): Alternate between exercises
    - Tri-set (3 exercises): Three exercises back-to-back
    - Giant set (4+ exercises): Multiple exercises as a circuit
    - Circuit: Any number of exercises performed in sequence

    Example JSON format:
    ```json
    {
        "superset": {
            "name": "Chest & Back Superset",
            "exercises": [
                {"name": "Push Up", "exercise_template_id": "392887AA", "sets": 3, "reps": 10},
                {"name": "Pull Up", "exercise_template_id": "ABC12345", "sets": 3, "reps": 8}
            ]
        }
    }
    ```

    Or using the circuit format:
    ```json
    {
        "circuit": {
            "name": "Core Circuit",
            "rounds": 3,
            "exercises": [
                {"name": "Plank", "exercise_template_id": "C6C9B8A0", "reps": "30 seconds"},
                {"name": "Crunches", "exercise_template_id": "DEF67890", "reps": 15},
                {"name": "Mountain Climbers", "exercise_template_id": "GHI11111", "reps": 20}
            ]
        }
    }
    ```
    """

    name: str = ""
    exercises: list[dict[str, Any]] = Field(default_factory=list)
    rounds: int = 1
    rest_between_exercises: int = 0
    rest_between_rounds: int = 60

    def get_exercise_count(self) -> int:
        """Return the number of exercises in the superset."""
        return len(self.exercises)

    def is_superset(self) -> bool:
        """Return True if this is a standard superset (2 exercises)."""
        return len(self.exercises) == 2

    def is_triset(self) -> bool:
        """Return True if this is a tri-set (3 exercises)."""
        return len(self.exercises) == 3

    def is_giant_set(self) -> bool:
        """Return True if this is a giant set (4+ exercises)."""
        return len(self.exercises) >= 4

    def get_superset_type(self) -> str:
        """Return a descriptive name for the superset type."""
        count = len(self.exercises)
        if count == 2:
            return "Superset"
        elif count == 3:
            return "Tri-set"
        elif count >= 4:
            return "Giant Set / Circuit"
        return "Single Exercise"

    @classmethod
    def from_json(cls, data: dict[str, Any], is_circuit: bool = False) -> "Superset":
        """Create a Superset from JSON data.

        Args:
            data: Dictionary containing superset/circuit definition
            is_circuit: If True, treat 'sets' as rounds (repeating all exercises)
        """
        rounds = 1
        if is_circuit:
            rounds = data.get("rounds", data.get("sets", 1))

        return cls(
            name=data.get("name", ""),
            exercises=data.get("exercises", []),
            rounds=rounds,
            rest_between_exercises=data.get("rest_between_exercises", 0),
            rest_between_rounds=data.get("rest_between_rounds", 60),
        )

    def expand_exercises(self, superset_id: int) -> list[dict[str, Any]]:
        """Expand the superset into individual exercises with superset_id.

        For circuits with multiple rounds, each exercise gets sets = rounds.
        For supersets, exercises keep their original sets.

        Args:
            superset_id: The ID to assign to all exercises in this group

        Returns:
            List of exercise dicts with superset_id applied
        """
        expanded = []
        for exercise in self.exercises:
            ex = exercise.copy()
            ex["superset_id"] = superset_id

            # For circuits, multiply sets by rounds
            if self.rounds > 1:
                original_sets = ex.get("sets", 1)
                ex["sets"] = original_sets * self.rounds

            # Apply rest between exercises (overrides individual rest)
            if self.rest_between_exercises > 0:
                ex["rest_seconds"] = self.rest_between_exercises

            expanded.append(ex)

        return expanded
