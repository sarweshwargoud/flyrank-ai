from fastapi import FastAPI

app = FastAPI()

# In-memory data (our temporary database)
tasks = [
    {
        "id": 1,
        "title": "Learn FastAPI",
        "done": False
    },
    {
        "id": 2,
        "title": "Learn CRUD",
        "done": False
    },
    {
        "id": 3,
        "title": "Submit Assignment",
        "done": True
    }
]

@app.get("/")
def home():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

@app.get("/tasks/{task_id}")
def get_tasks(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return {"error": "Task not found"}