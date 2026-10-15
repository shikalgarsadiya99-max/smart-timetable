from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/archive", tags=["archive"])


@router.post("/semester-over")
def semester_over(semester_label: str,
                  db: Session = Depends(get_db),
                  user: models.User = Depends(auth.get_current_admin)):
    """Archive current timetable and clear all working data."""
    # Get all timetable entries
    entries = db.query(models.TimetableEntry).all()
    if not entries:
        raise HTTPException(400, "No timetable to archive")

    # Serialize to JSON
    data = []
    for e in entries:
        course = db.query(models.Course).get(e.course_id)
        teacher = db.query(models.Teacher).get(e.teacher_id)
        room = db.query(models.Room).get(e.room_id)
        data.append({
            "day": e.day,
            "start_time": e.start_time,
            "end_time": e.end_time,
            "course_code": course.code if course else "",
            "course_name": course.name if course else "",
            "class_name": course.class_name if course else "",
            "course_type": course.course_type if course else "",
            "teacher_name": teacher.name if teacher else "",
            "room_name": room.name if room else "",
            "batch": e.batch
        })

    archive = models.ArchivedTimetable(
        semester_label=semester_label,
        data=json.dumps(data),
        created_at=datetime.now().isoformat()
    )
    db.add(archive)

    # Clear working data
    db.query(models.TimetableEntry).delete()
    db.query(models.Constraint).delete()
    db.query(models.Batch).delete()
    db.query(models.Division).delete()
    db.query(models.Course).delete()
    db.query(models.Teacher).delete()
    db.query(models.Room).delete()
    db.commit()

    return {"message": f"Semester '{semester_label}' archived successfully"}


@router.get("/", response_model=list[schemas.ArchivedTimetableResponse])
def get_archives(db: Session = Depends(get_db),
                 user: models.User = Depends(auth.get_current_admin)):
    return db.query(models.ArchivedTimetable).order_by(
        models.ArchivedTimetable.id.desc()
    ).all()


@router.get("/{archive_id}", response_model=schemas.ArchivedTimetableResponse)
def get_archive(archive_id: int,
                db: Session = Depends(get_db),
                user: models.User = Depends(auth.get_current_admin)):
    archive = db.query(models.ArchivedTimetable).get(archive_id)
    if not archive:
        raise HTTPException(404, "Archive not found")
    return archive