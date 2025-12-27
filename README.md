# Hevy API Integration

A Python toolkit for interacting with the Hevy workout app API. This project allows you to create workout routines in Hevy from structured JSON files.

## Features

-   Fetch exercise templates from Hevy API
-   Create workout routines from JSON files
-   Support for multi-day workout programs
-   Organize routines in folders based on program name
-   Handles various exercise types (reps, time-based, etc.)
-   Validates exercise template IDs

## Installation

### Requirements

-   Python 3.6+
-   `requests` library
-   `python-dotenv` library

### Setup

1. Clone this repository:

    ```
    git clone https://github.com/joshualukecaine/hevy.git
    cd hevy
    ```

2. Create a virtual environment and install dependencies:

    ```
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install requests python-dotenv
    ```

3. Create a `.env` file in the project root with your Hevy API key:

    ```
    HEVY_API_KEY=your_api_key_here
    ```

    To get your API key, log in to your Hevy account and follow their API key generation process.

## Usage

### Fetching Exercise Templates

Before creating routines, you should fetch the latest exercise templates from Hevy:

```bash
python src/fetch_templates.py
```

This will download all available exercise templates and save them to `data/exercise_templates.json`. The script will only update the file if it's older than 30 days or doesn't exist. Use the `--force` flag to update regardless of age.

Options:

-   `--force`: Force update even if the file is recent
-   `--output PATH`: Specify a different output file path

### Creating Routines

To create workout routines in Hevy from a JSON file:

```bash
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
        -   **category**: Exercise category (e.g., "Upper Body", "Core")
        -   **sets**: Number of sets
        -   **reps**: Number of reps or duration (e.g., 10, "30 seconds", "2 minutes")
        -   **rest_seconds**: Rest time between sets in seconds
        -   **notes**: Exercise notes
        -   **exercise_template_id**: Hevy exercise template ID

### Exercise Template IDs

Each exercise needs a valid Hevy exercise template ID. These IDs are 8-character hexadecimal strings (e.g., "79EF4E4F"). You can find these IDs in the `data/exercise_templates.json` file after running `fetch_templates.py`.

If you don't know the ID for an exercise, you can try to match it by name. The script will attempt to find a matching exercise template based on the exercise name.

## Examples

The `examples/routines` directory contains sample workout routines:

-   `simple_workout.json`: A basic two-day workout program
-   `runner_program.json`: A comprehensive 4-day runner's strength program

## Project Structure

```
hevy/
├── README.md                 # This file
├── .env                      # API key (create this file)
├── src/                      # Source code
│   ├── create_routine.py     # Script to create routines
│   ├── fetch_templates.py    # Script to fetch exercise templates
│   └── utils/                # Utility functions
│       ├── __init__.py       # Package initialization
│       └── hevy_api.py       # Common API functions
├── data/                     # Data directory
│   └── exercise_templates.json  # Exercise templates
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

1. The ID is an 8-character hexadecimal string
2. The ID exists in the Hevy system
3. The exercise name matches a known template if you're relying on name matching

### API Key Issues

If you get authentication errors, check that:

1. Your `.env` file exists in the project root
2. The file contains `HEVY_API_KEY=your_key_here`
3. The API key is valid and active

### Rate Limiting

The Hevy API may have rate limits. If you're creating many routines at once, you might hit these limits. Add delays between requests if needed.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
