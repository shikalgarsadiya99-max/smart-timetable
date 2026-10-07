from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.post("/", response_model=schemas.RoomResponse)
def create_room(data: schemas.RoomCreate,
                db: Session = Depends(get_db),
                user: models.User = Depends(auth.get_current_user)):
    if db.query(models.Room).filter(models.Room.name == data.name).first():
        raise HTTPException(400, "Room already exists")
    room = models.Room(**data.dict())
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.get("/", response_model=list[schemas.RoomResponse])
def get_rooms(db: Session = Depends(get_db),
              user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Room).all()


@router.delete("/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db),
                user: models.User = Depends(auth.get_current_user)):
    room = db.query(models.Room).get(room_id)
    if not room:
        raise HTTPException(404, "Room not found")
    db.delete(room)
    db.commit()
    return {"message": "Room deleted"}