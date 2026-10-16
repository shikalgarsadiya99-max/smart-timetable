from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/departments", tags=["departments"])


@router.post("/", response_model=schemas.DepartmentResponse)
def create_department(data: schemas.DepartmentCreate,
                      db: Session = Depends(get_db),
                      user: models.User = Depends(auth.get_current_admin)):
    if db.query(models.Department).filter(models.Department.name == data.name).first():
        raise HTTPException(400, "Department name already exists")
    if db.query(models.Department).filter(models.Department.code == data.code).first():
        raise HTTPException(400, "Department code already exists")
    dept = models.Department(**data.dict())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.get("/", response_model=list[schemas.DepartmentResponse])
def get_departments(db: Session = Depends(get_db)):
    return db.query(models.Department).all()


@router.delete("/{dept_id}")
def delete_department(dept_id: int,
                      db: Session = Depends(get_db),
                      user: models.User = Depends(auth.get_current_admin)):
    dept = db.query(models.Department).get(dept_id)
    if not dept:
        raise HTTPException(404, "Department not found")
    db.delete(dept)
    db.commit()
    return {"message": "Department deleted"}