from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db
from app.routes import router as task_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the SQLite database and seed initial values on startup
    init_db()
    yield


app = FastAPI(
    title="Task API",
    description="A simple CRUD API backed by SQLite for managing tasks.",
    version="1.0.0",
    lifespan=lifespan
)

# Register routes
app.include_router(task_router)


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
