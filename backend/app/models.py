from sqlalchemy import Column, Integer, String, ForeignKey
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="student")
    int_password = Column(Integer, nullable=True)
    department = Column(String, nullable=True)
    semester = Column(Integer, nullable=True)
    division = Column(String, nullable=True)
    batch = Column(String, nullable=True)


class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    department = Column(String)
    type = Column(String, default="internal")
    max_workload = Column(Integer, default=18)
    organization = Column(String, default="")


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    code = Column(String, unique=True)
    credits = Column(Integer, default=3)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    semester = Column(Integer)
    department = Column(String)
    class_name = Column(String)
    course_type = Column(String, default="theory")


class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    capacity = Column(Integer)
    type = Column(String, default="classroom")


class TimetableEntry(Base):
    __tablename__ = "timetable"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))
    day = Column(String)
    start_time = Column(String)
    end_time = Column(String)
    status = Column(String, default="confirmed")
    is_locked = Column(Integer, default=0)
    batch = Column(String, nullable=True)
    semester_label = Column(String, nullable=True)


class Division(Base):
    __tablename__ = "divisions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    department = Column(String)
    semester = Column(Integer)
    classroom = Column(String, nullable=True)
    total_students = Column(Integer, default=60)


class Batch(Base):
    __tablename__ = "batches"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    division_id = Column(Integer, ForeignKey("divisions.id"))


class Constraint(Base):
    __tablename__ = "constraints"
    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String)
    day = Column(String)
    start_time = Column(String)
    end_time = Column(String)
    is_active = Column(Integer, default=1)


class ArchivedTimetable(Base):
    __tablename__ = "archived_timetables"
    id = Column(Integer, primary_key=True, index=True)
    semester_label = Column(String)
    data = Column(String)
    created_at = Column(String)


class Settings(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True)
    value = Column(String)


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    code = Column(String, unique=True)
    hod = Column(String, nullable=True)