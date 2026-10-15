from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from . import models  # noqa
from .routers import users, teachers, courses, rooms, timetable
from .routers import divisions, batches, constraints, archive

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Timetable API",
    description="Backend for Smart Timetable Management System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(users.router)
app.include_router(teachers.router)
app.include_router(courses.router)
app.include_router(rooms.router)
app.include_router(timetable.router)
app.include_router(divisions.router)
app.include_router(batches.router)
app.include_router(constraints.router)
app.include_router(archive.router)


@app.get("/")
def root():
    return {
        "message": "Smart Timetable API v1.0 is running!",
        "status": "success",
        "version": "1.0.0"
    }


@app.get("/api/health")
def health():
    return {"status": "healthy", "version": "1.0.0"}