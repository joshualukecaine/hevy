#!/usr/bin/env python3
"""
Fetch Exercise Templates from Hevy API

This script fetches all exercise templates from the Hevy API and saves them to a local JSON file
for future reference. This allows for offline mapping of exercise names to template IDs.

Usage:
    python fetch_exercise_templates.py [--force] [--output OUTPUT]

Options:
    --force             Force update even if the file exists and is recent
    --output OUTPUT     Specify the output file (default: exercise_templates.json)
"""

import os
import json
import argparse
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

def load_api_key():
    """Load the Hevy API key from the .env file."""
    load_dotenv()
    api_key = os.getenv("HEVY_API_KEY")
    if not api_key:
        raise ValueError("HEVY_API_KEY not found in .env file")
    return api_key

def fetch_exercise_templates(api_key):
    """Fetch all exercise templates from the Hevy API."""
    url = "https://api.hevyapp.com/v1/exercise_templates"
    headers = {"api-key": api_key}
    all_templates = []
    current_page = 1
    
    try:
        while True:
            print(f"Fetching page {current_page}...")
            response = requests.get(
                url, 
                headers=headers, 
                params={"page": current_page, "per_page": 100}
            )
            response.raise_for_status()  # Raise an exception for 4XX/5XX responses
            
            data = response.json()
            templates = data.get("exercise_templates", [])
            all_templates.extend(templates)
            
            # Check if we've reached the last page
            if current_page >= data.get("page_count", current_page):
                break
                
            current_page += 1
        
        print(f"Fetched a total of {len(all_templates)} exercise templates")
        return all_templates
    except requests.exceptions.RequestException as e:
        print(f"Error fetching exercise templates: {e}")
        raise

def save_templates(templates, output_file):
    """Save exercise templates to a JSON file with metadata."""
    # Add metadata
    data = {
        "metadata": {
            "last_updated": datetime.now().isoformat(),
            "count": len(templates)
        },
        "templates": templates
    }
    
    # Create directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved {len(templates)} exercise templates to {output_file}")

def should_update(output_file, force=False):
    """Determine if we should update the templates file."""
    if force:
        return True
    
    if not os.path.exists(output_file):
        return True
    
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if the file has metadata and is recent (within 30 days)
        if "metadata" in data and "last_updated" in data["metadata"]:
            last_updated = datetime.fromisoformat(data["metadata"]["last_updated"])
            days_since_update = (datetime.now() - last_updated).days
            
            if days_since_update < 30:
                print(f"Exercise templates file is {days_since_update} days old.")
                print("Use --force to update anyway.")
                return False
    except (json.JSONDecodeError, KeyError, ValueError):
        # If there's any issue with the file, update it
        return True
    
    return True

def main():
    """Main function to fetch and save exercise templates."""
    parser = argparse.ArgumentParser(description="Fetch exercise templates from Hevy API")
    parser.add_argument("--force", action="store_true", help="Force update even if file exists and is recent")
    parser.add_argument("--output", default="./data/exercise_templates.json", help="Output file path")
    args = parser.parse_args()
    
    if not should_update(args.output, args.force):
        return
    
    try:
        api_key = load_api_key()
        templates = fetch_exercise_templates(api_key)
        save_templates(templates, args.output)
        print("Exercise templates updated successfully!")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
