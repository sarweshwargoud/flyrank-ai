from fastapi import FastAPI
from app.auth import supabase

app = FastAPI(
    title="FlyRank Week 4 Auth API",
    description="Authentication and protected routes using Supabase Auth and FastAPI.",
    version="1.0.0"
)


@app.get("/", summary="Root Endpoint")
def root():
    return {
        "name": "FlyRank Auth API",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health", summary="Health Check")
def health_check():
    return {
        "status": "ok",
        "supabase": "connected" if supabase else "disconnected"
    }
