from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/teachers", tags=["teachers"])


@router.post("/", response_model=schemas.TeacherResponse)
def create_teacher(data: schemas.TeacherCreate,
                   db: Session = Depends(get_db),
                   user: models.User = Depends(auth.get_current_user)):
    if db.query(models.Teacher).filter(models.Teacher.email == data.email).first():
        raise HTTPException(400, "Email already exists")
    teacher = models.Teacher(**data.dict())
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@router.get("/", response_model=list[schemas.TeacherResponse])
def get_teachers(db: Session = Depends(get_db),
                 user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Teacher).all()


@router.get("/external", response_model=list[schemas.TeacherResponse])
def get_external_teachers(db: Session = Depends(get_db),
                          user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Teacher).filter(models.Teacher.type == "external").all()


@router.get("/{teacher_id}", response_model=schemas.TeacherResponse)
def get_teacher(teacher_id: int, db: Session = Depends(get_db),
                user: models.User = Depends(auth.get_current_user)):
    teacher = db.query(models.Teacher).get(teacher_id)
    if not teacher:
        raise HTTPException(404, "Teacher not found")
    return teacher


@router.delete("/{teacher_id}")
def delete_teacher(teacher_id: int, db: Session = Depends(get_db),
                   user: models.User = Depends(auth.get_current_user)):
    teacher = db.query(models.Teacher).get(teacher_id)
    if not teacher:
        raise HTTPException(404, "Teacher not found")
    db.delete(teacher)
    db.commit()
    return {"message": "Teacher deleted successfully"}