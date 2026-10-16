from pydantic import BaseModel, EmailStr
from typing import Optional


# ========== USER ==========
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: str = "student"
    int_password: int
    department: Optional[str] = None
    semester: Optional[int] = None
    division: Optional[str] = None
    batch: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str
    int_password: int


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    department: Optional[str] = None
    semester: Optional[int] = None
    division: Optional[str] = None
    batch: Optional[str] = None

    class Config:
        from_attributes = True


# ========== TEACHER ==========
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


# ========== COURSE ==========
class CourseCreate(BaseModel):
    name: str
    code: str
    credits: int = 3
    teacher_id: int
    semester: int
    department: str
    class_name: str
    course_type: Optional[str] = "theory"


class CourseResponse(BaseModel):
    id: int
    name: str
    code: str
    credits: int
    teacher_id: int
    semester: int
    department: str
    class_name: str
    course_type: str

    class Config:
        from_attributes = True


# ========== ROOM ==========
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


# ========== TIMETABLE ==========
class TimetableCreate(BaseModel):
    course_id: int
    teacher_id: int
    room_id: int
    day: str
    start_time: str
    end_time: str
    batch: Optional[str] = None


class TimetableResponse(BaseModel):
    id: int
    course_id: int
    teacher_id: int
    room_id: int
    day: str
    start_time: str
    end_time: str
    status: str
    is_locked: int = 0
    batch: Optional[str] = None
    semester_label: Optional[str] = None

    class Config:
        from_attributes = True


class TimetableUpdate(BaseModel):
    day: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    room_id: Optional[int] = None
    status: Optional[str] = None


class TimetableLock(BaseModel):
    is_locked: int


# ========== DIVISION ==========
class DivisionCreate(BaseModel):
    name: str
    department: str
    semester: int
    classroom: Optional[str] = None
    total_students: Optional[int] = 60


class DivisionResponse(BaseModel):
    id: int
    name: str
    department: str
    semester: int
    classroom: Optional[str] = None
    total_students: int

    class Config:
        from_attributes = True


# ========== BATCH ==========
class BatchCreate(BaseModel):
    name: str
    division_id: int


class BatchResponse(BaseModel):
    id: int
    name: str
    division_id: int

    class Config:
        from_attributes = True


# ========== CONSTRAINT ==========
class ConstraintCreate(BaseModel):
    course_code: str
    day: str
    start_time: str
    end_time: str
    is_active: Optional[int] = 1


class ConstraintResponse(BaseModel):
    id: int
    course_code: str
    day: str
    start_time: str
    end_time: str
    is_active: int

    class Config:
        from_attributes = True


# ========== ARCHIVE ==========
class ArchivedTimetableResponse(BaseModel):
    id: int
    semester_label: str
    data: str
    created_at: str

    class Config:
        from_attributes = True


# ========== DEPARTMENT ==========
class DepartmentCreate(BaseModel):
    name: str
    code: str
    hod: Optional[str] = None


class DepartmentResponse(BaseModel):
    id: int
    name: str
    code: str
    hod: Optional[str] = None

    class Config:
        from_attributes = True