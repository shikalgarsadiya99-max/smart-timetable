from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/batches", tags=["batches"])


@router.post("/", response_model=schemas.BatchResponse)
def create_batch(data: schemas.BatchCreate,
                 db: Session = Depends(get_db),
                 user: models.User = Depends(auth.get_current_admin)):
    division = db.query(models.Division).get(data.division_id)
    if not division:
        raise HTTPException(404, "Division not found")
    existing = db.query(models.Batch).filter(
        models.Batch.name == data.name,
        models.Batch.division_id == data.division_id
    ).first()
    if existing:
        raise HTTPException(400, "Batch already exists in this division")
    batch = models.Batch(**data.dict())
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


@router.get("/", response_model=list[schemas.BatchResponse])
def get_batches(db: Session = Depends(get_db),
                user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Batch).all()


@router.get("/by-division/{division_id}", response_model=list[schemas.BatchResponse])
def get_batches_by_division(division_id: int,
                            db: Session = Depends(get_db),
                            user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Batch).filter(models.Batch.division_id == division_id).all()


@router.delete("/{batch_id}")
def delete_batch(batch_id: int,
                 db: Session = Depends(get_db),
                 user: models.User = Depends(auth.get_current_admin)):
    batch = db.query(models.Batch).get(batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")
    db.delete(batch)
    db.commit()
    return {"message": "Batch deleted"}