# Hevy Public API Documentation

## Authentication

All endpoints require your API key in the header:

```http
api-key: <your-uuid-key>
```

---

## Workouts

### Get a paginated list of workouts

**GET** `/v1/workouts`  
Retrieve your workouts in pages.

**Query Parameters (optional)**

-   `page` (integer): page number (default: 1)
-   `per_page` (integer): items per page (default: 20)

**Responses**

-   `200 OK` – JSON array of workout objects.

---

### Create a new workout

**POST** `/v1/workouts`  
Add a brand-new workout to your account.

**Request Body** (`application/json`)

```json
{
    "workout": {
        "title": "Friday Leg Day 🔥",
        "description": "Medium intensity leg day focusing on quads.",
        "start_time": "2024-08-14T12:00:00Z",
        "end_time": "2024-08-14T12:30:00Z",
        "is_private": false,
        "exercises": [
            {
                "exercise_template_id": "D04AC939",
                "superset_id": null,
                "notes": "Felt good today. Form was on point.",
                "sets": [
                    {
                        "type": "normal",
                        "weight_kg": 100,
                        "reps": 10,
                        "distance_meters": null,
                        "duration_seconds": null,
                        "custom_metric": null,
                        "rpe": null
                    }
                ]
            }
        ]
    }
}
```

**Responses**

-   `201 Created` – Returns the created Workout object.
-   `400 Bad Request` – Invalid request body.

---

### Get total number of workouts

**GET** `/v1/workouts/count`  
Fetch the total count of workouts you’ve logged.

**Responses**

-   `200 OK` – `{ "count": <integer> }`

---

### Get workout events since a date

**GET** `/v1/workouts/events`  
Retrieve a paged list of workout updates or deletes since a given timestamp.

**Query Parameters**

-   `since` (string, ISO 8601) – only events after this timestamp.
-   `page`, `per_page` – for pagination.

**Responses**

-   `200 OK` – JSON array of event objects (type “updated” or “deleted”).

---

### Update an existing workout

**PUT** `/v1/workouts/{workoutId}`  
Modify one of your workouts.

| Name      | In   | Type   | Required | Description                  |
| --------- | ---- | ------ | -------- | ---------------------------- |
| workoutId | path | string | yes      | ID of the workout to update. |

**Request Body** (`application/json`)

```json
{
    "workout": {
        /* see UpdatedWorkout schema */
    }
}
```

**Responses**

-   `200 OK` – Returns the updated Workout object.
-   `400 Bad Request` – Invalid request body.
-   `404 Not Found` – Workout not found or not yours.

---

## Exercise Templates

### Get all exercise templates

**GET** `/v1/exercise_templates`  
Retrieve the master list of all exercises you can add to workouts.

**Responses**

-   `200 OK` – JSON array of ExerciseTemplate objects.

---

### Get a single exercise template

**GET** `/v1/exercise_templates/{exerciseTemplateId}`  
Fetch details for one exercise template.

| Name               | In   | Type   | Required | Description                  |
| ------------------ | ---- | ------ | -------- | ---------------------------- |
| exerciseTemplateId | path | string | yes      | ID of the exercise template. |

**Responses**

-   `200 OK` – ExerciseTemplate object.
-   `404 Not Found` – Unknown template ID.

---

## Routines

### Get a paginated list of routines

**GET** `/v1/routines`  
List your saved routines.

**Query Parameters (optional)**

-   `page`, `per_page` – pagination
-   `folder_id` – filter by folder

**Responses**

-   `200 OK` – JSON array of Routine objects.

---

### Create a new routine

**POST** `/v1/routines`  
Define a brand-new routine.

**Request Body** (`application/json`)

```json
{
    "routine": {
        "title": "April Leg Day 🔥",
        "folder_id": null,
        "notes": "Focus on form over weight. Remember to stretch.",
        "exercises": [
            {
                "exercise_template_id": "D04AC939",
                "superset_id": null,
                "rest_seconds": 90,
                "notes": "Stay slow and controlled.",
                "sets": [
                    {
                        "type": "normal",
                        "weight_kg": 100,
                        "reps": 10,
                        "distance_meters": null,
                        "duration_seconds": null,
                        "custom_metric": null
                    }
                ]
            }
        ]
    }
}
```

**Responses**

-   `201 Created` – Returns the created Routine.
-   `400 Bad Request` – Invalid request body.
-   `403 Forbidden` – Routine limit exceeded.

---

### Get a single routine

**GET** `/v1/routines/{routineId}`  
Fetch one of your routines by ID.

| Name      | In   | Type   | Required | Description        |
| --------- | ---- | ------ | -------- | ------------------ |
| routineId | path | string | yes      | ID of the routine. |

**Responses**

-   `200 OK` – Routine object.
-   `404 Not Found` – Routine not found or not yours.

---

### Update an existing routine

**PUT** `/v1/routines/{routineId}`  
Modify an existing routine.

| Name      | In   | Type   | Required | Description        |
| --------- | ---- | ------ | -------- | ------------------ |
| routineId | path | string | yes      | ID of the routine. |

**Request Body** (`application/json`)

```json
{
    "routine": {
        "title": "April Leg Day 🔥",
        "notes": "Focus on form over weight. Remember to stretch.",
        "exercises": [
            {
                "exercise_template_id": "D04AC939",
                "superset_id": null,
                "rest_seconds": 90,
                "notes": "Stay slow and controlled.",
                "sets": [
                    {
                        "type": "normal",
                        "weight_kg": 100,
                        "reps": 10,
                        "distance_meters": null,
                        "duration_seconds": null,
                        "custom_metric": null
                    }
                ]
            }
        ]
    }
}
```

**Responses**

-   `200 OK` – Updated Routine object.
-   `400 Bad Request` – Invalid request body.
-   `403 Forbidden` – Routine limit exceeded.
-   `404 Not Found` – Routine not found or not yours.

---

## Routine Folders

### Get a paginated list of routine folders

**GET** `/v1/routine_folders`  
List folders you’ve created to organize routines.

**Query Parameters (optional)**

-   `page`, `per_page` – pagination

**Responses**

-   `200 OK` – JSON array of RoutineFolder objects.

---

### Create a new routine folder

**POST** `/v1/routine_folders`  
Make a new folder (it goes to index 0).

**Request Body** (`application/json`)

```json
{
    "routine_folder": {
        "title": "Push Pull 🏋️‍♂️"
    }
}
```

**Responses**

-   `201 Created` – Returns the new RoutineFolder.
-   `400 Bad Request` – Invalid request body.

---

### Get a single routine folder

**GET** `/v1/routine_folders/{folderId}`  
Fetch one folder by ID.

| Name     | In   | Type   | Required | Description               |
| -------- | ---- | ------ | -------- | ------------------------- |
| folderId | path | string | yes      | ID of the routine folder. |

**Responses**

-   `200 OK` – RoutineFolder object.
-   `404 Not Found` – Folder not found or not yours.
