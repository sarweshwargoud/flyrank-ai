from fastapi import FastAPI, HTTPException

app = FastAPI()

# In-memory database
tasks = [
    {
        "id": 1,
        "title": "Learn FastAPI",
        "done": False
    },
    {
        "id": 2,
        "title": "Build CRUD API",
        "done": False
    },
    {
        "id": 3,
        "title": "Submit Assignment",
        "done": True
    }
]


# Root Endpoint
@app.get("/")
def home():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": [
            "/tasks"
        ]
    }


# Health Check Endpoint
@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


# Get All Tasks
@app.get("/tasks")
def get_tasks():
    return tasks


# Get Single Task
@app.get("/tasks/{task_id}")
def get_task(task_id: int):

    for task in tasks:
        if task["id"] == task_id:
            return task

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )