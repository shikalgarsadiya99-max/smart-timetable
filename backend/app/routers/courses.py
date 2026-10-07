from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.post("/", response_model=schemas.CourseResponse)
def create_course(data: schemas.CourseCreate,
                  db: Session = Depends(get_db),
                  user: models.User = Depends(auth.get_current_user)):
    if db.query(models.Course).filter(models.Course.code == data.code).first():
        raise HTTPException(400, "Course code already exists")
    course = models.Course(**data.dict())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("/", response_model=list[schemas.CourseResponse])
def get_courses(db: Session = Depends(get_db),
                user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Course).all()


@router.delete("/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db),
                  user: models.User = Depends(auth.get_current_user)):
    course = db.query(models.Course).get(course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    db.delete(course)
    db.commit()
    return {"message": "Course deleted"}