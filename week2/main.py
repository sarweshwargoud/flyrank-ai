from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel

app = FastAPI()

# -----------------------------
# Request Model
# -----------------------------
class TaskCreate(BaseModel):
    title: str


# -----------------------------
# Update Model
# -----------------------------
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
@app.get("/")
def home():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
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


# Create Task
@app.post("/tasks", status_code=status.HTTP_201_CREATED)
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


# Update Task
@app.put("/tasks/{task_id}")
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


# Delete Task
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            return Response(status_code=204)

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )