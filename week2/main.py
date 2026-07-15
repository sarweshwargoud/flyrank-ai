from fastapi import FastAPI, HTTPException, status, Response
from pydantic import BaseModel

app = FastAPI(
    title="Task API",
    description="A simple CRUD API built using FastAPI for managing tasks.",
    version="1.0.0"
)

# -----------------------------
# Request Models
# -----------------------------
class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str
    done: bool


# -----------------------------
# In-memory Database
# -----------------------------
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


# -----------------------------
# Root Endpoint
# -----------------------------
@app.get(
    "/",
    summary="API Information",
    description="Returns basic information about the Task API."
)
def home():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }


# -----------------------------
# Health Check
# -----------------------------
@app.get(
    "/health",
    summary="Health Check",
    description="Checks whether the API server is running."
)
def health_check():
    return {
        "status": "ok"
    }


# -----------------------------
# Get All Tasks
# -----------------------------
@app.get(
    "/tasks",
    summary="Get All Tasks",
    description="Returns all tasks stored in the in-memory database."
)
def get_tasks():
    return tasks


# -----------------------------
# Get Single Task
# -----------------------------
@app.get(
    "/tasks/{task_id}",
    summary="Get Task By ID",
    description="Returns a single task using its ID."
)
def get_task(task_id: int):

    for task in tasks:
        if task["id"] == task_id:
            return task

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )


# -----------------------------
# Create Task
# -----------------------------
@app.post(
    "/tasks",
    status_code=status.HTTP_201_CREATED,
    summary="Create Task",
    description="Creates a new task with a unique ID and marks it as not completed."
)
def create_task(task: TaskCreate):

    if task.title.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty"
        )

    new_id = max((task["id"] for task in tasks), default=0) + 1

    new_task = {
        "id": new_id,
        "title": task.title,
        "done": False
    }

    tasks.append(new_task)

    return new_task


# -----------------------------
# Update Task
# -----------------------------
@app.put(
    "/tasks/{task_id}",
    summary="Update Task",
    description="Updates the title and completion status of an existing task."
)
def update_task(task_id: int, updated_task: TaskUpdate):

    if updated_task.title.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty"
        )

    for task in tasks:

        if task["id"] == task_id:

            task["title"] = updated_task.title
            task["done"] = updated_task.done

            return task

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )


# -----------------------------
# Delete Task
# -----------------------------
@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Task",
    description="Deletes a task from the in-memory database."
)
def delete_task(task_id: int):

    for task in tasks:

        if task["id"] == task_id:

            tasks.remove(task)

            return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )