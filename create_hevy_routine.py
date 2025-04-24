#!/usr/bin/env python3
"""
Create Hevy Routine Script

Creates workout routines in Hevy from a JSON file with exercise data.

Usage:
    python create_hevy_routine.py [--input INPUT] [--title TITLE] [--notes NOTES]
"""

import os
import json
import argparse
import requests
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv


def load_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("HEVY_API_KEY")
    if not api_key:
        raise ValueError("HEVY_API_KEY not found in .env file")
    return api_key


def load_json_file(file_path: str) -> Dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading {file_path}: {e}")
        raise


def parse_duration_to_seconds(rep_value: str) -> int:
    if "minute" in rep_value.lower():
        try:
            return int(rep_value.split()[0]) * 60
        except (ValueError, IndexError):
            return 60
    elif "second" in rep_value.lower():
        try:
            return int(rep_value.split()[0])
        except (ValueError, IndexError):
            return 30
    return 0


def parse_reps(rep_value: Any) -> Dict:
    set_data = {
        "type": "normal",
        "weight_kg": None,
        "reps": None,
        "distance_meters": None,
        "duration_seconds": None,
        "custom_metric": None
    }

    if isinstance(rep_value, str):
        if "minute" in rep_value.lower() or "second" in rep_value.lower():
            set_data["duration_seconds"] = parse_duration_to_seconds(rep_value)
        else:
            try:
                set_data["reps"] = int(rep_value)
            except (ValueError, TypeError):
                set_data["reps"] = 1
    else:
        set_data["reps"] = rep_value

    return set_data


def convert_exercise_to_hevy_format(exercise: Dict) -> Optional[Dict]:
    if "exercise_template_id" not in exercise:
        return None

    sets = []
    for _ in range(exercise.get("sets", 1)):
        sets.append(parse_reps(exercise.get("reps", "")))

    rest_seconds = exercise.get("rest_seconds", 0)
    if isinstance(rest_seconds, str):
        try:
            rest_seconds = int(rest_seconds)
        except (ValueError, TypeError):
            rest_seconds = 0

    return {
        "exercise_template_id": exercise.get("exercise_template_id", ""),
        "superset_id": None,
        "rest_seconds": rest_seconds,
        "notes": exercise.get("notes", ""),
        "sets": sets
    }


def is_valid_hevy_id(template_id: str) -> bool:
    return len(template_id) == 8 and all(c in "0123456789ABCDEF" for c in template_id)


def get_exercise_templates() -> Dict[str, str]:
    try:
        with open("./data/exercise_templates.json", 'r', encoding='utf-8') as f:
            templates = json.load(f)

        return {
            template.get("title", "").lower(): template.get("id", "")
            for template in templates.get("templates", [])
        }
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def validate_exercise_id(exercise: Dict, name_to_id_map: Dict[str, str]) -> Optional[str]:
    template_id = exercise.get("exercise_template_id", "")

    if is_valid_hevy_id(template_id):
        return template_id

    exercise_name = exercise.get("name", "").lower()
    if exercise_name in name_to_id_map:
        valid_id = name_to_id_map[exercise_name]
        if is_valid_hevy_id(valid_id):
            return valid_id

    return None


def create_day_exercises(day: Dict, name_to_id_map: Dict[str, str]) -> List[Dict]:
    valid_exercises = []

    for exercise in day.get("exercises", []):
        if "exercise_template_id" not in exercise:
            continue

        exercise_data = convert_exercise_to_hevy_format(exercise)
        if not exercise_data:
            continue

        valid_id = validate_exercise_id(exercise, name_to_id_map)
        if valid_id:
            exercise_data["exercise_template_id"] = valid_id
            valid_exercises.append(exercise_data)
        else:
            print(f"Skipping exercise with invalid ID: {exercise.get('exercise_template_id')}")

    return valid_exercises


def create_routine_payload(exercises: List[Dict], title: str, notes: str) -> Dict:
    return {
        "routine": {
            "title": title,
            "folder_id": None,
            "notes": notes,
            "exercises": exercises
        }
    }


def post_routine_to_hevy(routine_data: Dict, api_key: str) -> Dict:
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }

    response = requests.post(
        "https://api.hevyapp.com/v1/routines",
        headers=headers,
        json=routine_data
    )

    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Error creating routine: {response.status_code} {response.text}")


def process_day(day_data: Dict, base_title: str, notes: str, name_to_id_map: Dict[str, str], api_key: str) -> str:
    day_number = day_data.get("day", 0)
    day_name = day_data.get("name", f"Day {day_number}")
    day_title = f"{base_title} - {day_name}"

    print(f"Creating routine '{day_title}'...")

    exercises = create_day_exercises(day_data, name_to_id_map)
    routine_payload = create_routine_payload(exercises, day_title, notes)

    response = post_routine_to_hevy(routine_payload, api_key)
    routine_id = response.get("routine", [{}])[0].get("id", "unknown")

    print(f"Routine added: {day_title} (ID: {routine_id})")
    return routine_id


def main():
    parser = argparse.ArgumentParser(description="Create Hevy routines from a workout JSON file")
    parser.add_argument("--input", default="routines/routine.json", help="Path to the routine JSON file")
    parser.add_argument("--title", default="", help="Base title for the routines")
    parser.add_argument("--notes", default="Created via API", help="Notes for the routines")
    args = parser.parse_args()

    try:
        print(f"Starting Hevy routine creation from {args.input}...")

        api_key = load_api_key()
        routine_data = load_json_file(args.input)
        name_to_id_map = get_exercise_templates()

        routine_ids = []
        for day_data in routine_data.get("days", []):
            routine_id = process_day(day_data, args.title, args.notes, name_to_id_map, api_key)
            routine_ids.append(routine_id)

        print(f"Done! Created {len(routine_ids)} routines in Hevy.")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
