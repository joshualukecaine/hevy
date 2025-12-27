# Hevy API Integration

A Python toolkit for interacting with the Hevy workout app API. This project allows you to create workout routines in Hevy from structured JSON files.

## Features

-   Fetch exercise templates from Hevy API
-   Create workout routines from JSON files
-   Support for multi-day workout programs
-   Organize routines in folders based on program name
-   Handles various exercise types (reps, time-based, etc.)
-   Validates exercise template IDs (supports both built-in and custom exercises)
-   Smart exercise matching and validation

## Installation

### Requirements

-   Python 3.6+
-   `requests` library
-   `python-dotenv` library

### Setup

1. Clone this repository:

    ```bash
    git clone https://github.com/joshualukecaine/hevy.git
    cd hevy
    ```

2. Create a virtual environment and install dependencies:

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install requests python-dotenv
    ```

3. Create a `.env` file in the project root with your Hevy API key:

    ```
    HEVY_API_KEY=your_api_key_here
    ```

    To get your API key, log in to your Hevy account at [https://hevyapp.com](https://hevyapp.com) and navigate to Settings > API to generate your key.

## Usage

### Fetching Exercise Templates

Before creating routines, you should fetch the latest exercise templates from Hevy:

```bash
source venv/bin/activate
python src/fetch_templates.py
```

This will download all available exercise templates (both built-in and custom) and save them to `data/exercise_templates.json`. The script will only update the file if it's older than 30 days or doesn't exist. Use the `--force` flag to update regardless of age.

Options:

-   `--force`: Force update even if the file is recent
-   `--output PATH`: Specify a different output file path

### Creating Routines

To create workout routines in Hevy from a JSON file:

```bash
source venv/bin/activate
python src/create_routine.py --input examples/routines/simple_workout.json
```

Each day in the input file will be created as a separate routine in Hevy. All routines are automatically organized in a folder in the Hevy app.

Options:

-   `--input PATH`: Path to the input JSON file (default: examples/routines/runner_program.json)
-   `--title TITLE`: Base title for the routines (default: "")
-   `--notes NOTES`: Notes to add to the routines (default: "Created via API")
-   `--folder NAME`: Custom folder name (defaults to program_name from the JSON file or a timestamp)
-   `--validate-only`: Only validate the routine without creating it (no API key needed)

The `--validate-only` flag is useful for checking your routine file for errors before attempting to create it in Hevy. This mode doesn't require an API key, making it perfect for validating routines during development or before sharing them.

## Routine JSON Format

The input JSON file should follow this structure:

```json
{
    "program_name": "Program Name",
    "program_description": "Program description",
    "days": [
        {
            "day": 1,
            "name": "Day Name",
            "description": "Day description",
            "duration_minutes": 45,
            "exercises": [
                {
                    "name": "Exercise Name",
                    "category": "Category",
                    "sets": 3,
                    "reps": 10,
                    "rest_seconds": 60,
                    "notes": "Exercise notes",
                    "exercise_template_id": "TEMPLATE_ID"
                }
            ]
        }
    ]
}
```

### Key Fields

-   **program_name**: Name of the overall program (also used as the folder name in Hevy)
-   **program_description**: Description of the program
-   **days**: Array of workout days
    -   **day**: Day number (1, 2, 3, etc.)
    -   **name**: Name of the workout day
    -   **description**: Description of the workout day
    -   **duration_minutes**: Estimated duration in minutes
    -   **exercises**: Array of exercises
        -   **name**: Exercise name
        -   **category**: Exercise category (e.g., "Upper Body", "Core", "Warm-up", "Finisher")
        -   **sets**: Number of sets
        -   **reps**: Number of reps or duration (e.g., 10, "30 seconds", "2 minutes", "40m")
        -   **rest_seconds**: Rest time between sets in seconds
        -   **notes**: Exercise notes
        -   **exercise_template_id**: Hevy exercise template ID

### Exercise Template IDs

Each exercise needs a valid Hevy exercise template ID. Hevy supports two ID formats:

1. **Built-in exercises**: 8-character hexadecimal strings (e.g., `3D0C7C75`, `F1E57334`)
2. **Custom exercises**: UUID format (e.g., `13084c79-fd76-432e-b7d6-4ad3c67ddf81`)

You can find these IDs in the `data/exercise_templates.json` file after running `fetch_templates.py`.

**Finding Exercise IDs:**

```bash
# Search for an exercise by name
grep -i "goblet squat" data/exercise_templates.json

# Or use Python to search more easily
python3 -c "
import json
data = json.load(open('data/exercise_templates.json'))
search = 'pull up'
matches = [ex for ex in data['templates'] if search in ex['title'].lower()]
for m in matches[:5]:
    print(f\"{m['title']}: {m['id']}\")
"
```

If you don't know the exact ID for an exercise, the validation script will attempt to find matching exercise templates and suggest alternatives based on muscle group and equipment.

## Examples

The `examples/routines` directory contains sample workout routines:

-   `simple_workout.json`: A basic two-day workout program
-   `runner_program.json`: A comprehensive 4-day runner's strength program

## Workflow Example

Here's a complete workflow for creating a new workout program:

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Fetch latest exercise templates
python src/fetch_templates.py --force

# 3. Create your routine JSON file (or use an example)
# Edit your_routine.json with your workout structure

# 4. Validate your routine first
python src/create_routine.py --input your_routine.json --validate-only

# 5. If validation passes, create the routines in Hevy
python src/create_routine.py --input your_routine.json
```

## Project Structure

```
hevy/
├── README.md                 # This file
├── .env                      # API key (create this file)
├── venv/                     # Virtual environment (created during setup)
├── src/                      # Source code
│   ├── create_routine.py     # Script to create routines
│   ├── fetch_templates.py    # Script to fetch exercise templates
│   └── utils/                # Utility functions
│       ├── __init__.py       # Package initialization
│       └── hevy_api.py       # Common API functions
├── data/                     # Data directory
│   └── exercise_templates.json  # Exercise templates (generated)
├── examples/                 # Example files
│   ├── routines/             # Example routine files
│   │   ├── runner_program.json  # Runner's program example
│   │   └── simple_workout.json  # Simple workout example
│   └── outputs/              # Example output files
└── docs/                     # Documentation
    └── hevy-api.md           # API documentation
```

## Troubleshooting

### Invalid Exercise Template ID

If you see "Skipping exercise with invalid ID" messages, it means the exercise template ID is not valid. Check that:

1. **For built-in exercises**: The ID is an 8-character hexadecimal string (e.g., `3D0C7C75`)
2. **For custom exercises**: The ID is in UUID format (e.g., `13084c79-fd76-432e-b7d6-4ad3c67ddf81`)
3. The ID exists in your Hevy account (run `fetch_templates.py --force` to refresh)
4. The exercise name matches a known template if you're relying on name matching

### API Key Issues

If you get authentication errors, check that:

1. Your `.env` file exists in the project root
2. The file contains `HEVY_API_KEY=your_key_here`
3. The API key is valid and active in your Hevy account

### Rate Limiting

The Hevy API may have rate limits. If you're creating many routines at once, you might hit these limits. The script includes appropriate delays between requests, but if you encounter issues, try creating routines in smaller batches.

### Custom Exercises Not Found

If you have custom exercises in your Hevy account that aren't being found:

1. Make sure you've run `fetch_templates.py --force` to get the latest exercise list
2. Check that the exercise exists in your Hevy account
3. Verify the exercise ID matches exactly (UUIDs are case-sensitive)

## Tips

-   **Use `--validate-only` first**: Always validate your routine file before creating it to catch errors early
-   **Organize with categories**: Use consistent category names ("Warm-up", "Main Work", "Finisher") for better organization
-   **Document with notes**: Add detailed notes to exercises for form cues and reminders
-   **Supersets and circuits**: Use `rest_seconds: 0` between exercises to indicate they should be done back-to-back
-   **Fetch templates regularly**: Run `fetch_templates.py --force` periodically to keep your local exercise database up to date

## License

This project is licensed under the MIT License - see the LICENSE file for details.
