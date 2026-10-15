from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/constraints", tags=["constraints"])


@router.post("/", response_model=schemas.ConstraintResponse)
def create_constraint(data: schemas.ConstraintCreate,
                      db: Session = Depends(get_db),
                      user: models.User = Depends(auth.get_current_admin)):
    constraint = models.Constraint(**data.dict())
    db.add(constraint)
    db.commit()
    db.refresh(constraint)
    return constraint


@router.get("/", response_model=list[schemas.ConstraintResponse])
def get_constraints(db: Session = Depends(get_db),
                    user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Constraint).filter(models.Constraint.is_active == 1).all()


@router.delete("/{constraint_id}")
def delete_constraint(constraint_id: int,
                      db: Session = Depends(get_db),
                      user: models.User = Depends(auth.get_current_admin)):
    constraint = db.query(models.Constraint).get(constraint_id)
    if not constraint:
        raise HTTPException(404, "Constraint not found")
    db.delete(constraint)
    db.commit()
    return {"message": "Constraint deleted"}