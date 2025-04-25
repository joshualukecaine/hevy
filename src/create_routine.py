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


def find_alternatives(exercise: Dict, templates: List[Dict]) -> List[Dict]:
    """Find alternative exercises based on muscle group and equipment."""
    muscle_group = exercise.get("match_info", {}).get("primary_muscle_group")
    equipment = exercise.get("match_info", {}).get("equipment")
    
    if not (muscle_group and equipment):
        return []
        
    return [
        {
            "title": t["title"],
            "id": t["id"],
            "muscle_group": t["primary_muscle_group"],
            "equipment": t["equipment"]
        }
        for t in templates
        if t["primary_muscle_group"] == muscle_group 
        and t["equipment"] == equipment
    ][:30]  # Get up to 30 alternatives for pagination


def show_alternatives_page(alternatives: List[Dict], page: int, page_size: int = 5) -> Tuple[bool, int]:
    """Show a page of alternatives and return if there are more pages."""
    start_idx = page * page_size
    end_idx = start_idx + page_size
    current_alternatives = alternatives[start_idx:end_idx]
    
    if not current_alternatives:
        return False, 0
        
    total_pages = (len(alternatives) + page_size - 1) // page_size
    print(f"\nShowing alternatives (Page {page + 1}/{total_pages}):")
    for i, alt in enumerate(current_alternatives, start=start_idx + 1):
        print(f"{i}. {alt['title']}")
        
    return end_idx < len(alternatives), total_pages


def validate_routine(routine_data: Dict, templates: List[Dict]) -> List[Dict]:
    """Validate all exercises in a routine against the templates database."""
    template_ids = {t["id"] for t in templates}
    invalid_exercises = []

    for day_idx, day in enumerate(routine_data.get("days", [])):
        day_name = day.get("name", f"Day {day.get('day', 0)}")

        for ex_idx, exercise in enumerate(day.get("exercises", [])):
            template_id = exercise.get("exercise_template_id", "")
            name = exercise.get("name", "")

            if not is_valid_hevy_id(template_id):
                alternatives = find_alternatives(exercise, templates)
                invalid_exercises.append({
                    "day": day_name,
                    "name": name,
                    "id": template_id,
                    "reason": "Invalid ID format - must be 8 hexadecimal characters",
                    "alternatives": alternatives,
                    "day_index": day_idx,
                    "exercise_index": ex_idx
                })
            elif template_id not in template_ids:
                alternatives = find_alternatives(exercise, templates)
                invalid_exercises.append({
                    "day": day_name,
                    "name": name,
                    "id": template_id,
                    "reason": "ID not found in exercise templates",
                    "alternatives": alternatives,
                    "day_index": day_idx,
                    "exercise_index": ex_idx
                })

    return invalid_exercises


def apply_fixes(routine_data: Dict, invalid_exercises: List[Dict], input_file: str) -> bool:
    """Apply fixes to the routine based on suggested alternatives."""
    if not invalid_exercises:
        return False
        
    print("\nOptions:")
    print("- Enter 'y' to fix exercises one by one")
    print("- Enter 'auto' to use the first alternative for all exercises")
    print("- Enter 'n' to skip fixing")
    
    choice = input("\nWhat would you like to do? ").lower().strip()
    if choice == 'n':
        return False
        
    changes_made = False
    
    if choice == 'auto':
        # Apply first alternative for all exercises
        for ex in invalid_exercises:
            if ex['alternatives']:
                alt = ex['alternatives'][0]
                routine_data['days'][ex['day_index']]['exercises'][ex['exercise_index']]['exercise_template_id'] = alt['id']
                print(f"Fixed {ex['name']} in {ex['day']} with {alt['title']}")
                changes_made = True
    elif choice == 'y':
        # Fix exercises one by one
        for exercise in invalid_exercises:
            if not exercise['alternatives']:
                print(f"\nSkipping {exercise['name']} (no alternatives available)")
                continue
                
            print(f"\nFixing {exercise['name']} in {exercise['day']}...")
            page = 0
            page_size = 5
            has_more, total_pages = show_alternatives_page(exercise['alternatives'], page, page_size)
            
            while True:
                if has_more:
                    print("\nEnter number to select, 'n' for next page, 'p' for previous page, or press Enter to skip:")
                else:
                    print("\nEnter number to select, 'p' for previous page, or press Enter to skip:")
                    
                choice = input().strip()
                
                if not choice:  # Skip this exercise
                    print("Skipping this exercise...")
                    break
                elif choice == 'n' and has_more:
                    page += 1
                    has_more, _ = show_alternatives_page(exercise['alternatives'], page, page_size)
                elif choice == 'p' and page > 0:
                    page -= 1
                    has_more, _ = show_alternatives_page(exercise['alternatives'], page, page_size)
                else:
                    try:
                        num = int(choice)
                        if 1 <= num <= len(exercise['alternatives']):
                            alt = exercise['alternatives'][num - 1]
                            routine_data['days'][exercise['day_index']]['exercises'][exercise['exercise_index']]['exercise_template_id'] = alt['id']
                            print(f"Fixed {exercise['name']} with {alt['title']}")
                            changes_made = True
                            break
                        else:
                            print("Invalid number. Please try again.")
                    except ValueError:
                        if choice not in ['n', 'p']:
                            print("Invalid input. Please try again.")
                
    if changes_made:
        print(f"\nSaving updated routine to {input_file}...")
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(routine_data, f, indent=4)
        print("Routine updated successfully!")
        
    return changes_made


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
    """Print formatted validation errors."""
    print("\nFound invalid exercises:")
    for exercise in invalid_exercises:
        print(f"\n{exercise['day']} - {exercise['name']} (ID: {exercise['id']})")
        print(f"  Reason: {exercise['reason']}")


def show_alternatives_page(alternatives: List[Dict], page: int, page_size: int = 5) -> Tuple[bool, int]:
    """Show a page of alternatives and return if there are more pages."""
    start_idx = page * page_size
    end_idx = start_idx + page_size
    current_alternatives = alternatives[start_idx:end_idx]
    
    if not current_alternatives:
        return False, 0
        
    total_pages = (len(alternatives) + page_size - 1) // page_size
    print(f"\nShowing alternatives (Page {page + 1}/{total_pages}):")
    for i, alt in enumerate(current_alternatives, start=start_idx + 1):
        print(f"{i}. {alt['title']}")
        
    return end_idx < len(alternatives), total_pages


def apply_fixes(routine_data: Dict, invalid_exercises: List[Dict], input_file: str) -> bool:
    """Apply fixes to the routine based on suggested alternatives."""
    if not invalid_exercises:
        return False
        
    print_validation_errors(invalid_exercises)
    print("\nOptions:")
    print("- Enter 'y' to fix exercises one by one")
    print("- Enter 'auto' to use the first alternative for all exercises")
    print("- Enter 'n' to skip fixing")
    
    choice = input("\nWhat would you like to do? ").lower().strip()
    if choice == 'n':
        return False
        
    changes_made = False
    
    if choice == 'auto':
        # Apply first alternative for all exercises
        for ex in invalid_exercises:
            if ex['alternatives']:
                alt = ex['alternatives'][0]
                routine_data['days'][ex['day_index']]['exercises'][ex['exercise_index']]['exercise_template_id'] = alt['id']
                print(f"Fixed {ex['name']} in {ex['day']} with {alt['title']}")
                changes_made = True
    elif choice == 'y':
        # Fix exercises one by one
        for exercise in invalid_exercises:
            if not exercise['alternatives']:
                print(f"\nSkipping {exercise['name']} (no alternatives available)")
                continue
                
            print(f"\nFixing {exercise['name']} in {exercise['day']}...")
            page = 0
            page_size = 5
            has_more, total_pages = show_alternatives_page(exercise['alternatives'], page, page_size)
            
            while True:
                if has_more:
                    print("\nEnter number to select, 'n' for next page, 'p' for previous page, or press Enter to skip:")
                else:
                    print("\nEnter number to select" + (" 'p' for previous page, " if page > 0 else "") + "or press Enter to skip:")
                    
                choice = input().strip()
                
                if not choice:  # Skip this exercise
                    print("Skipping this exercise...")
                    break
                elif choice == 'n' and has_more:
                    page += 1
                    has_more, _ = show_alternatives_page(exercise['alternatives'], page, page_size)
                elif choice == 'p' and page > 0:
                    page -= 1
                    has_more, _ = show_alternatives_page(exercise['alternatives'], page, page_size)
                else:
                    try:
                        num = int(choice)
                        if 1 <= num <= len(exercise['alternatives']):
                            alt = exercise['alternatives'][num - 1]
                            routine_data['days'][exercise['day_index']]['exercises'][exercise['exercise_index']]['exercise_template_id'] = alt['id']
                            print(f"Fixed {exercise['name']} with {alt['title']}")
                            changes_made = True
                            break
                        else:
                            print("Invalid number. Please try again.")
                    except ValueError:
                        if choice not in ['n', 'p']:
                            print("Invalid input. Please try again.")
                
    if changes_made:
        print(f"\nSaving updated routine to {input_file}...")
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(routine_data, f, indent=4)
        print("Routine updated successfully!")
        
    return changes_made


def main():
    """Main function to create Hevy routines from a workout JSON file."""
    parser = argparse.ArgumentParser(description="Create Hevy routines from a workout JSON file")
    parser.add_argument("--input", default="./examples/routines/runner_program.json", help="Path to the routine JSON file")
    parser.add_argument("--title", default="", help="Base title for the routines")
    parser.add_argument("--notes", default="Created via API", help="Notes for the routines")
    parser.add_argument("--folder", help="Custom folder name (defaults to program_name or timestamp)")
    parser.add_argument("--validate-only", action="store_true", help="Only validate the routine without creating it")
    args = parser.parse_args()

    try:
        print(f"Starting Hevy routine {'validation' if args.validate_only else 'creation'} from {args.input}...")
        
        routine_data = load_json_file(args.input)
        
        with open("./data/exercise_templates.json", 'r', encoding='utf-8') as f:
            templates = json.load(f)["templates"]
            
        invalid_exercises = validate_routine(routine_data, templates)
        if invalid_exercises:
            print_validation_errors(invalid_exercises)
            if apply_fixes(routine_data, invalid_exercises, args.input):
                # Re-validate after fixes
                invalid_exercises = validate_routine(routine_data, templates)
                if not invalid_exercises:
                    print("\nAll exercises are now valid!")
                    if args.validate_only:
                        return 0
                else:
                    raise ValueError("Some exercises still have invalid IDs")
            else:
                raise ValueError("Invalid exercises found in routine")
            
        if args.validate_only:
            print("\nValidation successful! All exercises are valid.")
            return 0
            
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
