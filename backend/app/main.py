from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import database and models
from .database import engine, Base
from . import models  # noqa: F401  (needed to register models)

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Timetable API",
    description="Backend for Smart Timetable Management System",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Smart Timetable API is running!",
        "status": "success",
        "version": "0.2.0",
        "database": "connected"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "smart-timetable-backend",
        "version": "0.2.0"
    }