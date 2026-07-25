from fastapi import APIRouter, HTTPException, status, Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.service import TaskService

router = APIRouter()
service = TaskService()


# -----------------------------
# Pydantic Schemas
# -----------------------------
class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str
    done: bool


# -----------------------------
# Endpoints
# -----------------------------

@router.get(
    "/tasks",
    summary="Get All Tasks",
    description="Returns all tasks stored in the SQLite database, with optional search and filter parameters."
)
def get_tasks(
    search: Optional[str] = None,
    done: Optional[bool] = None,
    sort: Optional[str] = None
):
    # Map 'done' query param correctly (since FastAPI handles conversion of string to bool)
    return service.get_all_tasks(search=search, done=done, sort_by=sort)


@router.get(
    "/tasks/{task_id}",
    summary="Get Task By ID",
    description="Returns a single task using its ID."
)
def get_task(task_id: int):
    task = service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    return task


@router.post(
    "/tasks",
    status_code=status.HTTP_201_CREATED,
    summary="Create Task",
    description="Creates a new task with a unique ID and marks it as not completed."
)
def create_task(task: TaskCreate):
    try:
        return service.create_task(task.title)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/tasks/{task_id}",
    summary="Update Task",
    description="Updates the title and completion status of an existing task."
)
def update_task(task_id: int, updated_task: TaskUpdate):
    try:
        task = service.update_task(task_id, updated_task.title, updated_task.done)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        return task
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Task",
    description="Deletes a task from the SQLite database."
)
def delete_task(task_id: int):
    deleted = service.delete_task(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/stats",
    summary="Get Task Stats",
    description="Returns aggregate statistics of the tasks in the database."
)
def get_stats():
    return service.get_stats()
