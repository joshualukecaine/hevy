"""Routine and workout program models."""

from pydantic import BaseModel, Field

from hevy.models.exercise import Exercise
from hevy.models.superset import Superset


class WorkoutDay(BaseModel):
    """Represents a single workout day in a program."""

    day: int
    name: str
    description: str = ""
    duration_minutes: int = 0
    exercises: list[Exercise] = Field(default_factory=list)

    @classmethod
    def from_json(cls, data: dict) -> "WorkoutDay":
        """Create WorkoutDay from JSON routine format.

        Supports both regular exercises and supersets/circuits:

        Regular exercise:
        ```json
        {"name": "Push Up", "exercise_template_id": "392887AA", "sets": 3, "reps": 10}
        ```

        Superset:
        ```json
        {
            "superset": {
                "exercises": [
                    {"name": "Push Up", "exercise_template_id": "392887AA", "sets": 3, "reps": 10},
                    {"name": "Pull Up", "exercise_template_id": "ABC12345", "sets": 3, "reps": 8}
                ]
            }
        }
        ```

        Circuit:
        ```json
        {
            "circuit": {
                "rounds": 3,
                "exercises": [
                    {"name": "Burpees", "exercise_template_id": "DEF67890", "reps": 10},
                    {"name": "Squats", "exercise_template_id": "GHI11111", "reps": 15}
                ]
            }
        }
        ```
        """
        exercises = []
        superset_counter = 1  # Hevy uses 1-based superset IDs

        for item in data.get("exercises", []):
            # Check if this is a superset
            if "superset" in item:
                superset = Superset.from_json(item["superset"], is_circuit=False)
                expanded = superset.expand_exercises(superset_counter)
                for ex_data in expanded:
                    exercises.append(Exercise.from_json(ex_data, superset_id=superset_counter))
                superset_counter += 1

            # Check if this is a circuit
            elif "circuit" in item:
                circuit = Superset.from_json(item["circuit"], is_circuit=True)
                expanded = circuit.expand_exercises(superset_counter)
                for ex_data in expanded:
                    exercises.append(Exercise.from_json(ex_data, superset_id=superset_counter))
                superset_counter += 1

            # Regular exercise
            else:
                exercises.append(Exercise.from_json(item))

        return cls(
            day=data.get("day", 0),
            name=data.get("name", f"Day {data.get('day', 0)}"),
            description=data.get("description", ""),
            duration_minutes=data.get("duration_minutes", 0),
            exercises=exercises,
        )


class WorkoutProgram(BaseModel):
    """Represents a complete workout program."""

    program_name: str
    program_description: str = ""
    days: list[WorkoutDay] = Field(default_factory=list)

    @classmethod
    def from_json(cls, data: dict) -> "WorkoutProgram":
        """Create WorkoutProgram from JSON file format."""
        days = [WorkoutDay.from_json(d) for d in data.get("days", [])]
        return cls(
            program_name=data.get("program_name", "Untitled Program"),
            program_description=data.get("program_description", ""),
            days=days,
        )

    def get_all_exercises(self) -> list[Exercise]:
        """Get all exercises across all days."""
        exercises = []
        for day in self.days:
            exercises.extend(day.exercises)
        return exercises

    def get_all_template_ids(self) -> set[str]:
        """Get all unique exercise template IDs in the program."""
        return {ex.exercise_template_id for ex in self.get_all_exercises()}


class Routine(BaseModel):
    """Represents a routine in Hevy (API format)."""

    id: str | None = None
    title: str
    folder_id: str | None = None
    notes: str = ""
    exercises: list[Exercise] = Field(default_factory=list)

    def to_api_format(self) -> dict:
        """Convert to Hevy API request format."""
        return {
            "routine": {
                "title": self.title,
                "folder_id": self.folder_id,
                "notes": self.notes,
                "exercises": [ex.to_api_format() for ex in self.exercises],
            }
        }

    @classmethod
    def from_workout_day(
        cls,
        day: WorkoutDay,
        base_title: str = "",
        notes: str = "",
        folder_id: str | None = None,
    ) -> "Routine":
        """Create a Routine from a WorkoutDay."""
        title = f"{base_title} - {day.name}" if base_title else day.name
        return cls(
            title=title,
            folder_id=folder_id,
            notes=notes or day.description,
            exercises=day.exercises,
        )


class RoutineFolder(BaseModel):
    """Represents a routine folder in Hevy."""

    id: str | None = None
    title: str
    index: int = 0

    def to_api_format(self) -> dict:
        """Convert to Hevy API request format."""
        return {
            "routine_folder": {
                "title": self.title,
            }
        }
