from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/timetable", tags=["timetable"])


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


def is_slot_available(db, day, start_time, teacher_id, room_id, class_name, exclude_id=None):
    query = db.query(models.TimetableEntry).filter(
        models.TimetableEntry.day == day,
        models.TimetableEntry.start_time == start_time
    )
    if exclude_id is not None:
        query = query.filter(models.TimetableEntry.id != exclude_id)
    for entry in query.all():
        if entry.teacher_id == teacher_id:
            return False
        if entry.room_id == room_id:
            return False
        course = db.query(models.Course).get(entry.course_id)
        if course and course.class_name == class_name:
            return False
    return True


@router.get("/", response_model=List[schemas.TimetableResponse])
def get_all(db: Session = Depends(get_db),
            user: models.User = Depends(auth.get_current_user)):
    return db.query(models.TimetableEntry).all()


@router.get("/class/{class_name}", response_model=List[schemas.TimetableResponse])
def get_by_class(class_name: str, db: Session = Depends(get_db),
                 user: models.User = Depends(auth.get_current_user)):
    courses = db.query(models.Course).filter(models.Course.class_name == class_name).all()
    course_ids = [c.id for c in courses]
    return db.query(models.TimetableEntry).filter(
        models.TimetableEntry.course_id.in_(course_ids)
    ).all()


@router.post("/auto-generate")
def auto_generate(db: Session = Depends(get_db),
                  user: models.User = Depends(auth.get_current_admin)):
    """Generate timetable - each course appears credits times per week."""
    
    # Delete only UNLOCKED entries
    db.query(models.TimetableEntry).filter(
        models.TimetableEntry.is_locked != 1
    ).delete()
    db.commit()
    
    courses = db.query(models.Course).all()
    rooms = db.query(models.Room).all()

    if not courses:
        raise HTTPException(400, "No courses found")
    if not rooms:
        raise HTTPException(400, "No rooms found")

    # Get locked entries and reserve their slots
    locked_entries = db.query(models.TimetableEntry).filter(
        models.TimetableEntry.is_locked == 1
    ).all()
    
    used_teacher = set()
    used_room = set()
    used_class = set()
    
    for e in locked_entries:
        used_teacher.add((e.day, e.start_time, e.teacher_id))
        used_room.add((e.day, e.start_time, e.room_id))
        course = db.query(models.Course).get(e.course_id)
        if course:
            used_class.add((e.day, e.start_time, course.class_name))

    created = []
    unplaced = []
    room_idx = 0

    # Each course placed 'credits' times per week
    for course in courses:
        sessions_needed = course.credits if course.credits and course.credits > 0 else 1
        sessions_placed = 0
        days_used_for_course = set()
        
        for day in DAYS:
            if sessions_placed >= sessions_needed:
                break
            if day in days_used_for_course:
                continue
            
            placed_this_day = False
            for (start, end) in SLOTS:
                tkey = (day, start, course.teacher_id)
                ckey = (day, start, course.class_name)

                if tkey in used_teacher or ckey in used_class:
                    continue

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

                entry = models.TimetableEntry(
                    course_id=course.id,
                    teacher_id=course.teacher_id,
                    room_id=chosen_room.id,
                    day=day,
                    start_time=start,
                    end_time=end,
                    status="confirmed",
                    is_locked=0
                )
                db.add(entry)
                used_teacher.add(tkey)
                used_room.add((day, start, chosen_room.id))
                used_class.add(ckey)
                created.append(entry)
                sessions_placed += 1
                days_used_for_course.add(day)
                placed_this_day = True
                break
            
            if not placed_this_day:
                continue

        if sessions_placed < sessions_needed:
            unplaced.append(f"{course.code} ({sessions_placed}/{sessions_needed})")

    db.commit()

    return {
        "message": "Timetable generated successfully",
        "total_courses": len(courses),
        "placed": len(created),
        "locked_preserved": len(locked_entries),
        "unplaced": unplaced,
        "unplaced_count": len(unplaced)
    }


@router.put("/{entry_id}", response_model=schemas.TimetableResponse)
def update_entry(entry_id: int,
                 data: schemas.TimetableUpdate,
                 db: Session = Depends(get_db),
                 user: models.User = Depends(auth.get_current_admin)):
    entry = db.query(models.TimetableEntry).get(entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")

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

    course = db.query(models.Course).get(entry.course_id)
    class_name = course.class_name if course else ""

    if not is_slot_available(db, entry.day, entry.start_time,
                             entry.teacher_id, entry.room_id,
                             class_name, entry.id):
        db.rollback()
        raise HTTPException(400, "Conflict: slot busy")

    db.commit()
    db.refresh(entry)
    return entry


@router.put("/{entry_id}/lock")
def toggle_lock(entry_id: int,
                data: schemas.TimetableLock,
                db: Session = Depends(get_db),
                user: models.User = Depends(auth.get_current_admin)):
    entry = db.query(models.TimetableEntry).get(entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")
    entry.is_locked = data.is_locked
    db.commit()
    db.refresh(entry)
    return entry


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


@router.delete("/clear/all")
def clear_all(db: Session = Depends(get_db),
              user: models.User = Depends(auth.get_current_admin)):
    db.query(models.TimetableEntry).delete()
    db.commit()
    return {"message": "All timetable entries cleared"}
