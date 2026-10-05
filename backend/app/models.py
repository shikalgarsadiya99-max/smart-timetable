from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="student")  # admin, teacher, student


class Teacher(Base):
    __tablename__ = "teachers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    department = Column(String)


class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    code = Column(String, unique=True)
    credits = Column(Integer, default=3)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    semester = Column(Integer)


class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    capacity = Column(Integer)


class TimetableEntry(Base):
    __tablename__ = "timetable"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))
    day = Column(String)      # Monday, Tuesday, etc.
    start_time = Column(String)  # "09:00"
    end_time = Column(String)    # "10:00"