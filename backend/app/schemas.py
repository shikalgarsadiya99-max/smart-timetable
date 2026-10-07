from pydantic import BaseModel, EmailStr
from typing import Optional


# ---------- USER ----------
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


# ---------- TEACHER ----------
class TeacherCreate(BaseModel):
    name: str
    email: EmailStr
    department: str
    type: Optional[str] = "internal"
    max_workload: Optional[int] = 18
    organization: Optional[str] = ""


class TeacherResponse(BaseModel):
    id: int
    name: str
    email: str
    department: str
    type: str
    max_workload: int
    organization: str
    class Config:
        from_attributes = True


# ---------- COURSE ----------
class CourseCreate(BaseModel):
    name: str
    code: str
    credits: int = 3
    teacher_id: int
    semester: int
    department: str
    class_name: str


class CourseResponse(BaseModel):
    id: int
    name: str
    code: str
    credits: int
    teacher_id: int
    semester: int
    department: str
    class_name: str
    class Config:
        from_attributes = True


# ---------- ROOM ----------
class RoomCreate(BaseModel):
    name: str
    capacity: int
    type: Optional[str] = "classroom"


class RoomResponse(BaseModel):
    id: int
    name: str
    capacity: int
    type: str
    class Config:
        from_attributes = True


# ---------- TIMETABLE ----------
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
    status: str
    class Config:
        from_attributes = True


class TimetableUpdate(BaseModel):
    day: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    room_id: Optional[int] = None
    status: Optional[str] = None