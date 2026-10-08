from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/timetable", tags=["timetable"])


# ----- Configuration (could be moved to DB later) -----
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
SLOTS = [
    ("09:00", "10:00"),
    ("10:00", "11:00"),
    ("11:15", "12:15"),
    ("12:15", "13:15"),
    ("14:00", "15:00"),
    ("15:00", "16:00"),
    ("16:00", "17:00"),
]


# ----- Helper: Check if a slot is free -----
def is_slot_available(db, day, start_time, teacher_id, room_id, class_name, exclude_id=None):
    """Returns True if the given slot has NO conflicts."""
    query = db.query(models.TimetableEntry).filter(
        models.TimetableEntry.day == day,
        models.TimetableEntry.start_time == start_time
    )
    if exclude_id is not None:
        query = query.filter(models.TimetableEntry.id != exclude_id)

    for entry in query.all():
        # Teacher conflict
        if entry.teacher_id == teacher_id:
            return False
        # Room conflict
        if entry.room_id == room_id:
            return False
        # Class conflict
        course = db.query(models.Course).get(entry.course_id)
        if course and course.class_name == class_name:
            return False

    return True


# ----- GET all timetable entries -----
@router.get("/", response_model=List[schemas.TimetableResponse])
def get_all(db: Session = Depends(get_db),
            user: models.User = Depends(auth.get_current_user)):
    return db.query(models.TimetableEntry).all()


# ----- GET entries for a specific class -----
@router.get("/class/{class_name}", response_model=List[schemas.TimetableResponse])
def get_by_class(class_name: str, db: Session = Depends(get_db),
                 user: models.User = Depends(auth.get_current_user)):
    courses = db.query(models.Course).filter(models.Course.class_name == class_name).all()
    course_ids = [c.id for c in courses]
    return db.query(models.TimetableEntry).filter(
        models.TimetableEntry.course_id.in_(course_ids)
    ).all()


# ----- CSP-based auto-generation -----
@router.post("/auto-generate")
def auto_generate(db: Session = Depends(get_db),
                  user: models.User = Depends(auth.get_current_admin)):
    """
    Generate timetable automatically using constraint-based scheduling.
    Clears previous timetable and creates a new one.
    """
    # Clear previous timetable
    db.query(models.TimetableEntry).delete()
    db.commit()

    courses = db.query(models.Course).all()
    rooms = db.query(models.Room).all()

    if not courses:
        raise HTTPException(400, "No courses found. Add courses first.")
    if not rooms:
        raise HTTPException(400, "No rooms found. Add rooms first.")

    # Track used slots globally
    used_teacher = set()   # (day, start, teacher_id)
    used_room = set()      # (day, start, room_id)
    used_class = set()     # (day, start, class_name)

    created = []
    unplaced = []
    room_idx = 0

    for course in courses:
        placed = False
        for day in DAYS:
            if placed:
                break
            for (start, end) in SLOTS:
                tkey = (day, start, course.teacher_id)
                ckey = (day, start, course.class_name)

                # Skip if teacher or class busy
                if tkey in used_teacher or ckey in used_class:
                    continue

                # Find an available room with sufficient capacity
                chosen_room = None
                for i in range(len(rooms)):
                    r = rooms[(room_idx + i) % len(rooms)]
                    rkey = (day, start, r.id)
                    if rkey not in used_room:
                        chosen_room = r
                        room_idx = (room_idx + i + 1) % len(rooms)
                        break

                if chosen_room is None:
                    continue

                # Assign
                entry = models.TimetableEntry(
                    course_id=course.id,
                    teacher_id=course.teacher_id,
                    room_id=chosen_room.id,
                    day=day,
                    start_time=start,
                    end_time=end,
                    status="confirmed"
                )
                db.add(entry)
                used_teacher.add(tkey)
                used_room.add((day, start, chosen_room.id))
                used_class.add(ckey)
                created.append(entry)
                placed = True
                break

        if not placed:
            unplaced.append(course.code)

    db.commit()

    return {
        "message": "Timetable generated successfully",
        "total_courses": len(courses),
        "placed": len(created),
        "unplaced": unplaced,
        "unplaced_count": len(unplaced)
    }


# ----- Manual slot change -----
@router.put("/{entry_id}", response_model=schemas.TimetableResponse)
def update_entry(entry_id: int,
                 data: schemas.TimetableUpdate,
                 db: Session = Depends(get_db),
                 user: models.User = Depends(auth.get_current_admin)):
    """Move an entry to a new day/time/room with conflict validation."""
    entry = db.query(models.TimetableEntry).get(entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")

    # Apply changes
    if data.day:
        entry.day = data.day
    if data.start_time:
        entry.start_time = data.start_time
    if data.end_time:
        entry.end_time = data.end_time
    if data.room_id:
        entry.room_id = data.room_id
    if data.status:
        entry.status = data.status

    # Validate conflicts
    course = db.query(models.Course).get(entry.course_id)
    class_name = course.class_name if course else ""

    if not is_slot_available(db, entry.day, entry.start_time,
                             entry.teacher_id, entry.room_id,
                             class_name, entry.id):
        db.rollback()
        raise HTTPException(400, "Conflict: teacher, room, or class already busy at that slot")

    db.commit()
    db.refresh(entry)
    return entry


# ----- Delete entry -----
@router.delete("/{entry_id}")
def delete_entry(entry_id: int,
                 db: Session = Depends(get_db),
                 user: models.User = Depends(auth.get_current_admin)):
    entry = db.query(models.TimetableEntry).get(entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")
    db.delete(entry)
    db.commit()
    return {"message": "Entry deleted"}


# ----- Clear all -----
@router.delete("/clear/all")
def clear_all(db: Session = Depends(get_db),
              user: models.User = Depends(auth.get_current_admin)):
    db.query(models.TimetableEntry).delete()
    db.commit()
    return {"message": "All timetable entries cleared"}