# Hevy CLI

[![CI](https://github.com/joshualukecaine/hevy/actions/workflows/ci.yml/badge.svg)](https://github.com/joshualukecaine/hevy/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python CLI for creating workout routines in [Hevy](https://hevyapp.com) from JSON files. Supports supersets, circuits, and automatic validation.

## Installation

```bash
git clone https://github.com/joshualukecaine/hevy.git
cd hevy
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

Get your API key from [hevyapp.com](https://hevyapp.com) → Settings → API, then:

```bash
echo "HEVY_API_KEY=your_key_here" > .env
```

## Usage

```bash
# Fetch exercise templates (required before first use)
hevy fetch

# Validate a routine file
hevy validate --input workout.json

# Create routines in Hevy
hevy create --input workout.json
hevy create --input workout.json --folder "My Program"
```

## Routine Format

### Basic Exercise

```json
{
    "program_name": "My Program",
    "days": [
        {
            "day": 1,
            "name": "Upper Body",
            "exercises": [
                {
                    "name": "Push Up",
                    "exercise_template_id": "392887AA",
                    "sets": 3,
                    "reps": 10,
                    "rest_seconds": 60
                }
            ]
        }
    ]
}
```

### Superset

```json
{
    "superset": {
        "exercises": [
            {"name": "Push Up", "exercise_template_id": "392887AA", "sets": 3, "reps": 12},
            {"name": "Pull Up", "exercise_template_id": "ABC12345", "sets": 3, "reps": 8}
        ]
    }
}
```

### Circuit

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

### Duration-Based Exercises

Use strings for timed exercises:

```json
{"name": "Plank", "exercise_template_id": "C6C9B8A0", "sets": 3, "reps": "30 seconds"}
```

## Finding Exercise IDs

After running `hevy fetch`, search for exercises:

```bash
grep -i "squat" data/exercise_templates.json
```

Or use Python:

```python
import json
data = json.load(open('data/exercise_templates.json'))
for t in data['templates']:
    if 'squat' in t['title'].lower():
        print(f"{t['title']}: {t['id']}")
```

## Development

```bash
pip install -e ".[dev]"
make test        # Run tests
make lint        # Run linting
make format      # Format code
```

## License

MIT
