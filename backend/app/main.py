from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from . import models  # noqa
from .routers import users, teachers, courses, rooms, timetable

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Timetable API",
    description="Backend for Smart Timetable Management System",
    version="0.4.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(teachers.router)
app.include_router(courses.router)
app.include_router(rooms.router)
app.include_router(timetable.router)


@app.get("/")
def root():
    return {
        "message": "Smart Timetable API is running!",
        "status": "success",
        "version": "0.4.0"
    }


@app.get("/api/health")
def health():
    return {"status": "healthy", "version": "0.4.0"}