from pydantic import BaseModel, EmailStr
from typing import Optional


# ---------- USER SCHEMAS ----------
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: Optional[str] = "student"


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str

    class Config:
        from_attributes = True


# ---------- TEACHER SCHEMAS ----------
class TeacherCreate(BaseModel):
    name: str
    email: EmailStr
    department: str


class TeacherResponse(BaseModel):
    id: int
    name: str
    email: str
    department: str

    class Config:
        from_attributes = True


# ---------- COURSE SCHEMAS ----------
class CourseCreate(BaseModel):
    name: str
    code: str
    credits: int = 3
    teacher_id: int
    semester: int


class CourseResponse(BaseModel):
    id: int
    name: str
    code: str
    credits: int
    teacher_id: int
    semester: int

    class Config:
        from_attributes = True


# ---------- ROOM SCHEMAS ----------
class RoomCreate(BaseModel):
    name: str
    capacity: int


class RoomResponse(BaseModel):
    id: int
    name: str
    capacity: int

    class Config:
        from_attributes = True


# ---------- TIMETABLE SCHEMAS ----------
class TimetableCreate(BaseModel):
    course_id: int
    teacher_id: int
    room_id: int
    day: str
    start_time: str
    end_time: str


class TimetableResponse(BaseModel):
    id: int
    course_id: int
    teacher_id: int
    room_id: int
    day: str
    start_time: str
    end_time: str

    class Config:
        from_attributes = True