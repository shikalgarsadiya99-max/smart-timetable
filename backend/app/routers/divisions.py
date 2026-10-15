from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/divisions", tags=["divisions"])


@router.post("/", response_model=schemas.DivisionResponse)
def create_division(data: schemas.DivisionCreate,
                    db: Session = Depends(get_db),
                    user: models.User = Depends(auth.get_current_admin)):
    if db.query(models.Division).filter(models.Division.name == data.name).first():
        raise HTTPException(400, "Division already exists")
    division = models.Division(**data.dict())
    db.add(division)
    db.commit()
    db.refresh(division)
    return division


@router.get("/", response_model=list[schemas.DivisionResponse])
def get_divisions(db: Session = Depends(get_db),
                  user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Division).all()


@router.get("/by-class/{class_name}", response_model=schemas.DivisionResponse)
def get_division_by_class(class_name: str,
                          db: Session = Depends(get_db),
                          user: models.User = Depends(auth.get_current_user)):
    division = db.query(models.Division).filter(models.Division.name == class_name).first()
    if not division:
        raise HTTPException(404, "Division not found")
    return division


@router.delete("/{division_id}")
def delete_division(division_id: int,
                    db: Session = Depends(get_db),
                    user: models.User = Depends(auth.get_current_admin)):
    division = db.query(models.Division).get(division_id)
    if not division:
        raise HTTPException(404, "Division not found")
    # Also delete batches
    db.query(models.Batch).filter(models.Batch.division_id == division_id).delete()
    db.delete(division)
    db.commit()
    return {"message": "Division deleted"}