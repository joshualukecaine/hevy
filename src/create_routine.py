#!/usr/bin/env python3
"""
Create Hevy Routines

Creates workout routines in Hevy from a JSON file with exercise data.
Each day in the input file becomes a separate routine in Hevy.
All routines are organized in a folder named after the program_name in the JSON file.

Usage:
    python create_routine.py [--input INPUT] [--title TITLE] [--notes NOTES] [--folder FOLDER]
"""

import os
import json
import argparse
import datetime
from typing import Dict, List, Any, Optional, Tuple

from utils.hevy_api import (
    load_api_key, 
    load_json_file, 
    post_to_hevy, 
    is_valid_hevy_id,
    create_routine_folder
)


def validate_routine(routine_data: Dict, templates: List[Dict]) -> List[Dict]:
    """Validate all exercises in a routine against the templates database."""
    template_ids = {t["id"] for t in templates}
    invalid_exercises = []

    for day in routine_data.get("days", []):
        day_name = day.get("name", f"Day {day.get('day', 0)}")

        for exercise in day.get("exercises", []):
            template_id = exercise.get("exercise_template_id", "")
            name = exercise.get("name", "")

            if not is_valid_hevy_id(template_id):
                invalid_exercises.append({
                    "day": day_name,
                    "name": name,
                    "id": template_id,
                    "reason": "Invalid ID format - must be 8 hexadecimal characters"
                })
            elif template_id not in template_ids:
                muscle_group = exercise.get("match_info", {}).get("primary_muscle_group")
                equipment = exercise.get("match_info", {}).get("equipment")
                alternatives = []

                if muscle_group and equipment:
                    alternatives = [
                        t["title"] for t in templates
                        if t["primary_muscle_group"] == muscle_group 
                        and t["equipment"] == equipment
                    ][:3]

                invalid_exercises.append({
                    "day": day_name,
                    "name": name,
                    "id": template_id,
                    "reason": "ID not found in exercise templates",
                    "alternatives": alternatives
                })

    return invalid_exercises


def parse_duration_to_seconds(rep_value: str) -> int:
    """Convert duration strings like '5 minutes' or '30 seconds' to seconds."""
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
    """Parse rep values into the Hevy API format."""
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
    """Convert an exercise from the routine format to the Hevy API format."""
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


def get_exercise_templates() -> Dict[str, str]:
    """Load exercise templates from the JSON file and create a name-to-ID mapping."""
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
    """Validate and potentially fix exercise template IDs."""
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
    """Process all exercises for a day and return valid exercises."""
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


def create_routine_payload(exercises: List[Dict], title: str, notes: str, folder_id: Optional[str] = None) -> Dict:
    """Create the routine payload for the Hevy API."""
    return {
        "routine": {
            "title": title,
            "folder_id": folder_id,
            "notes": notes,
            "exercises": exercises
        }
    }


def process_day(day_data: Dict, base_title: str, notes: str, name_to_id_map: Dict[str, str], api_key: str, folder_id: Optional[str] = None) -> str:
    """Process a single day and create a routine in Hevy."""
    day_number = day_data.get("day", 0)
    day_name = day_data.get("name", f"Day {day_number}")
    
    # Only add the base_title and separator if base_title is not empty
    if base_title:
        day_title = f"{base_title} - {day_name}"
    else:
        day_title = day_name
    
    print(f"Creating routine '{day_title}'...")
    
    exercises = create_day_exercises(day_data, name_to_id_map)
    routine_payload = create_routine_payload(exercises, day_title, notes, folder_id)
    
    response = post_to_hevy("routines", routine_payload, api_key)
    routine_id = response.get("routine", [{}])[0].get("id", "unknown")
    
    print(f"Routine added: {day_title} (ID: {routine_id})")
    return routine_id


def print_validation_errors(invalid_exercises: List[Dict]) -> None:
    """Print formatted validation errors with suggested alternatives."""
    print("\nFound invalid exercises:")
    for exercise in invalid_exercises:
        print(f"\n{exercise['day']} - {exercise['name']} (ID: {exercise['id']})")
        print(f"  Reason: {exercise['reason']}")
        if exercise.get('alternatives'):
            print("  Suggested alternatives:")
            for alt in exercise['alternatives']:
                print(f"  - {alt}")


def main():
    """Main function to create Hevy routines from a workout JSON file."""
    parser = argparse.ArgumentParser(description="Create Hevy routines from a workout JSON file")
    parser.add_argument("--input", default="./examples/routines/runner_program.json", help="Path to the routine JSON file")
    parser.add_argument("--title", default="", help="Base title for the routines")
    parser.add_argument("--notes", default="Created via API", help="Notes for the routines")
    parser.add_argument("--folder", help="Custom folder name (defaults to program_name or timestamp)")
    args = parser.parse_args()

    try:
        print(f"Starting Hevy routine creation from {args.input}...")
        
        routine_data = load_json_file(args.input)
        
        with open("./data/exercise_templates.json", 'r', encoding='utf-8') as f:
            templates = json.load(f)["templates"]
            
        invalid_exercises = validate_routine(routine_data, templates)
        if invalid_exercises:
            print_validation_errors(invalid_exercises)
            raise ValueError("Invalid exercises found in routine")
            
        api_key = load_api_key()
        name_to_id_map = {t["title"].lower(): t["id"] for t in templates}
        
        folder_name = args.folder or routine_data.get("program_name") or f"Routines {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        print(f"\nCreating routine folder '{folder_name}'...")
        folder_id = create_routine_folder(folder_name, api_key)
        print(f"Folder created with ID: {folder_id}")
        
        routine_ids = []
        for day_data in routine_data.get("days", []):
            routine_id = process_day(day_data, args.title, args.notes, name_to_id_map, api_key, folder_id)
            routine_ids.append(routine_id)
        
        print(f"\nDone! Created {len(routine_ids)} routines in folder '{folder_name}'.")
        return 0
        
    except Exception as e:
        print(f"\nError: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
