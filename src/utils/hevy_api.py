"""
Hevy API Utilities

Common functions for interacting with the Hevy API.
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv


def load_api_key() -> str:
    """Load the Hevy API key from the .env file."""
    load_dotenv()
    api_key = os.getenv("HEVY_API_KEY")
    if not api_key:
        raise ValueError("HEVY_API_KEY not found in .env file")
    return api_key


def load_json_file(file_path: str) -> Dict:
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading {file_path}: {e}")
        raise


def post_to_hevy(endpoint: str, data: Dict, api_key: str) -> Dict:
    """Post data to the Hevy API."""
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    
    response = requests.post(
        f"https://api.hevyapp.com/v1/{endpoint}",
        headers=headers,
        json=data
    )
    
    if response.status_code in (200, 201):
        return response.json()
    else:
        raise Exception(f"API error: {response.status_code} {response.text}")


def get_from_hevy(endpoint: str, api_key: str, params: Optional[Dict] = None) -> Dict:
    """Get data from the Hevy API."""
    headers = {
        "api-key": api_key
    }
    
    response = requests.get(
        f"https://api.hevyapp.com/v1/{endpoint}",
        headers=headers,
        params=params
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API error: {response.status_code} {response.text}")


def is_valid_hevy_id(template_id: str) -> bool:
    """Check if the template ID is a valid Hevy ID format.
    
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
    # Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    if len(template_id) == 36 and template_id.count('-') == 4:
        parts = template_id.split('-')
        if len(parts) == 5 and len(parts[0]) == 8 and len(parts[1]) == 4 and len(parts[2]) == 4 and len(parts[3]) == 4 and len(parts[4]) == 12:
            return all(c in "0123456789ABCDEFabcdef-" for c in template_id)
    
    return False


def create_routine_folder(title: str, api_key: str) -> str:
    """Create a routine folder and return its ID."""
    payload = {
        "routine_folder": {
            "title": title
        }
    }
    
    response = post_to_hevy("routine_folders", payload, api_key)
    folder_id = response.get("routine_folder", {}).get("id")
    
    if not folder_id:
        raise Exception("Failed to create routine folder")
        
    return folder_id
