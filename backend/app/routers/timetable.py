from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from io import BytesIO
from fpdf import FPDF
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/timetable", tags=["timetable"])

# Tuesday to Saturday (Sunday + Monday off)
DAYS = ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

SLOTS = [
    ("09:00", "10:00"),
    ("10:00", "11:00"),
    ("11:15", "12:15"),
    ("12:15", "13:15"),
    ("14:00", "15:00"),
    ("15:00", "16:00"),
    ("16:00", "17:00"),
]


def is_lab_course(course):
    """Detect lab course by type OR by name containing 'lab'"""
    if not course:
        return False
    if course.course_type and course.course_type.lower() == "lab":
        return True
    if course.name and "lab" in course.name.lower():
        return True
    if course.code and "lab" in course.code.lower():
        return True
    return False


def find_free_room(rooms, day, slot_times, used_rooms, room_type=None, preferred=None):
    """Find a free room for a set of slots. Prefer preferred name if given."""
    if preferred:
        for room in rooms:
            if room.name == preferred:
                free = all((day, t, room.id) not in used_rooms for t in slot_times)
                if free:
                    return room
                break
    for room in rooms:
        if room_type and room.type != room_type:
            continue
        free = all((day, t, room.id) not in used_rooms for t in slot_times)
        if free:
            return room
    return None


@router.get("/", response_model=List[schemas.TimetableResponse])
def get_all(db: Session = Depends(get_db),
            user: models.User = Depends(auth.get_current_user)):
    if user.role == "student":
        courses = db.query(models.Course).filter(
            models.Course.class_name == user.division
        ).all()
        course_ids = [c.id for c in courses]
        return db.query(models.TimetableEntry).filter(
            models.TimetableEntry.course_id.in_(course_ids)
        ).all()
    elif user.role == "teacher":
        # Match teacher by email or username (name)
        teacher = db.query(models.Teacher).filter(
            (models.Teacher.email == user.email) |
            (models.Teacher.name.ilike(f"%{user.username}%"))
        ).first()
        if not teacher:
            return []
        return db.query(models.TimetableEntry).filter(
            models.TimetableEntry.teacher_id == teacher.id
        ).all()
    return db.query(models.TimetableEntry).all()


@router.get("/class/{class_name}", response_model=List[schemas.TimetableResponse])
def get_by_class(class_name: str,
                 db: Session = Depends(get_db),
                 user: models.User = Depends(auth.get_current_user)):
    courses = db.query(models.Course).filter(models.Course.class_name == class_name).all()
    course_ids = [c.id for c in courses]
    return db.query(models.TimetableEntry).filter(
        models.TimetableEntry.course_id.in_(course_ids)
    ).all()


@router.post("/auto-generate")
def auto_generate(db: Session = Depends(get_db),
                  user: models.User = Depends(auth.get_current_admin)):
    db.query(models.TimetableEntry).filter(
        models.TimetableEntry.is_locked != 1
    ).delete()
    db.commit()

    courses = db.query(models.Course).all()
    rooms = db.query(models.Room).all()
    divisions = db.query(models.Division).all()
    constraints = db.query(models.Constraint).filter(
        models.Constraint.is_active == 1
    ).all()

    if not courses:
        raise HTTPException(400, "No courses found")
    if not rooms:
        raise HTTPException(400, "No rooms found")

    division_map = {d.name: d for d in divisions}

    locked_entries = db.query(models.TimetableEntry).filter(
        models.TimetableEntry.is_locked == 1
    ).all()

    used_teacher = set()
    used_room = set()
    used_class = set()

    for e in locked_entries:
        used_teacher.add((e.day, e.start_time, e.teacher_id))
        used_room.add((e.day, e.start_time, e.room_id))
        c = db.query(models.Course).get(e.course_id)
        if c:
            used_class.add((e.day, e.start_time, c.class_name))

    created = []
    unplaced = []
    constraint_applied = []

    # APPLY CONSTRAINTS FIRST (case-insensitive match)
    for course in courses:
        match = next(
            (cs for cs in constraints
             if cs.course_code.strip().lower() == (course.code or "").strip().lower()),
            None
        )
        if not match:
            continue

        day = match.day
        start = match.start_time
        end = match.end_time

        if day not in DAYS:
            unplaced.append(f"{course.code} (invalid day {day})")
            continue

        slot_times = []
        for (s, e) in SLOTS:
            if s >= start and s < end:
                slot_times.append(s)
        if not slot_times:
            slot_times = [start]

        teacher_busy = any((day, t, course.teacher_id) in used_teacher for t in slot_times)
        if teacher_busy:
            unplaced.append(f"{course.code} (teacher busy at constraint)")
            continue

        class_busy = any((day, t, course.class_name) in used_class for t in slot_times)
        if class_busy:
            unplaced.append(f"{course.code} (class busy at constraint)")
            continue

        division = division_map.get(course.class_name)
        preferred = division.classroom if division else None
        room = find_free_room(rooms, day, slot_times, used_room, preferred=preferred)
        if not room:
            room = find_free_room(rooms, day, slot_times, used_room)
        if not room:
            unplaced.append(f"{course.code} (no room at constraint)")
            continue

        entry = models.TimetableEntry(
            course_id=course.id,
            teacher_id=course.teacher_id,
            room_id=room.id,
            day=day,
            start_time=start,
            end_time=end,
            status="confirmed",
            is_locked=1
        )
        db.add(entry)
        for t in slot_times:
            used_teacher.add((day, t, course.teacher_id))
            used_room.add((day, t, room.id))
            used_class.add((day, t, course.class_name))
        created.append(entry)
        constraint_applied.append(course.code)

    # Split theory vs lab
    theory_courses = [c for c in courses if not is_lab_course(c)]
    lab_courses = [c for c in courses if is_lab_course(c)]

    constrained_codes = {cs.course_code.strip().lower() for cs in constraints}
    theory_courses = [c for c in theory_courses if (c.code or "").strip().lower() not in constrained_codes]
    lab_courses = [c for c in lab_courses if (c.code or "").strip().lower() not in constrained_codes]

    # THEORY: place credits sessions, each 1 hour
    for course in theory_courses:
        needed = course.credits or 1
        placed = 0
        days_used = set()
        division = division_map.get(course.class_name)
        preferred = division.classroom if division else None

        for day in DAYS:
            if placed >= needed:
                break
            if day in days_used:
                continue
            for (start, end) in SLOTS:
                if (day, start, course.teacher_id) in used_teacher:
                    continue
                if (day, start, course.class_name) in used_class:
                    continue
                room = find_free_room(rooms, day, [start], used_room, preferred=preferred)
                if not room:
                    room = find_free_room(rooms, day, [start], used_room, room_type="classroom")
                if not room:
                    continue
                entry = models.TimetableEntry(
                    course_id=course.id, teacher_id=course.teacher_id,
                    room_id=room.id, day=day, start_time=start, end_time=end,
                    is_locked=0, batch=None
                )
                db.add(entry)
                used_teacher.add((day, start, course.teacher_id))
                used_room.add((day, start, room.id))
                used_class.add((day, start, course.class_name))
                created.append(entry)
                placed += 1
                days_used.add(day)
                break
        if placed < needed:
            unplaced.append(f"{course.code} theory ({placed}/{needed})")

    # LAB: place credits sessions, each 2-hour block
    for course in lab_courses:
        needed = course.credits or 1
        placed = 0
        days_used = set()
        division = division_map.get(course.class_name)
        preferred = division.classroom if division else None

        for day in DAYS:
            if placed >= needed:
                break
            if day in days_used:
                continue

            for i in range(len(SLOTS) - 1):
                start1 = SLOTS[i][0]
                end2 = SLOTS[i + 1][1]
                slot_times = [SLOTS[i][0], SLOTS[i + 1][0]]

                if any((day, t, course.teacher_id) in used_teacher for t in slot_times):
                    continue
                if any((day, t, course.class_name) in used_class for t in slot_times):
                    continue

                room = find_free_room(rooms, day, slot_times, used_room,
                                      room_type="lab", preferred=preferred)
                if not room:
                    room = find_free_room(rooms, day, slot_times, used_room,
                                          room_type="lab")
                if not room:
                    continue

                entry = models.TimetableEntry(
                    course_id=course.id, teacher_id=course.teacher_id,
                    room_id=room.id, day=day,
                    start_time=start1, end_time=end2,
                    is_locked=0, batch=None
                )
                db.add(entry)
                for t in slot_times:
                    used_teacher.add((day, t, course.teacher_id))
                    used_room.add((day, t, room.id))
                    used_class.add((day, t, course.class_name))
                created.append(entry)
                placed += 1
                days_used.add(day)
                break

        if placed < needed:
            unplaced.append(f"{course.code} lab ({placed}/{needed})")

    db.commit()

    return {
        "message": "Timetable generated successfully",
        "total_courses": len(courses),
        "placed": len(created),
        "locked_preserved": len(locked_entries),
        "constraints_applied": constraint_applied,
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
    if data.day: entry.day = data.day
    if data.start_time: entry.start_time = data.start_time
    if data.end_time: entry.end_time = data.end_time
    if data.room_id: entry.room_id = data.room_id
    if data.status: entry.status = data.status
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
    return {"message": "All cleared"}


# ============ COLORFUL PDF EXPORT ============
@router.get("/export/pdf")
def export_pdf(db: Session = Depends(get_db),
               user: models.User = Depends(auth.get_current_user)):
    entries = db.query(models.TimetableEntry).all()

    if user.role == "student":
        courses_q = db.query(models.Course).filter(
            models.Course.class_name == user.division
        ).all()
        course_ids = [c.id for c in courses_q]
        entries = [e for e in entries if e.course_id in course_ids]
    elif user.role == "teacher":
        teacher = db.query(models.Teacher).filter(
            (models.Teacher.email == user.email) |
            (models.Teacher.name.ilike(f"%{user.username}%"))
        ).first()
        if teacher:
            entries = [e for e in entries if e.teacher_id == teacher.id]
        else:
            entries = []

    courses = {c.id: c for c in db.query(models.Course).all()}
    teachers = {t.id: t for t in db.query(models.Teacher).all()}
    rooms = {r.id: r for r in db.query(models.Room).all()}

    # Color palette per course
    PALETTE = [
        (219, 234, 254),
        (254, 243, 199),
        (220, 252, 231),
        (237, 233, 254),
        (255, 228, 230),
        (254, 226, 226),
        (224, 242, 254),
        (252, 231, 243),
    ]
    course_ids = sorted(courses.keys())
    color_map = {cid: PALETTE[i % len(PALETTE)] for i, cid in enumerate(course_ids)}

    # PDF setup
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()

    # Title banner
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 297, 22, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_xy(0, 5)
    pdf.cell(297, 12, "SMART TIMETABLE", align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(0, 16)
    pdf.cell(297, 5, "Smart Timetable Management System", align="C")

    pdf.ln(18)
    pdf.set_text_color(30, 64, 175)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"User: {user.username}   |   Role: {user.role.upper()}", ln=True, align="C")
    pdf.set_text_color(100, 116, 139)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "Academic Year: 2026-2027   |   Kolhapur Institute of Technology", ln=True, align="C")
    pdf.ln(3)

    # Merged slots (matching browser)
    SLOTS_PDF = [
        {"start": "09:00", "end": "10:00", "label": "09:00-10:00", "span": 1},
        {"start": "10:00", "end": "11:00", "label": "10:00-11:00", "span": 1},
        {"start": "11:15", "end": "13:15", "label": "11:15-13:15", "span": 2},
        {"start": "14:00", "end": "15:00", "label": "14:00-15:00", "span": 1},
        {"start": "15:00", "end": "16:00", "label": "15:00-16:00", "span": 1},
        {"start": "16:00", "end": "17:00", "label": "16:00-17:00", "span": 1},
    ]

    DAYS_PDF = ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    time_w = 26
    day_w = (277 - time_w) / len(DAYS_PDF)
    row_h = 18
    merged_row_h = 36

    # Header row
    pdf.set_fill_color(30, 64, 175)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_x(10)
    pdf.cell(time_w, 10, "TIME", border=1, align="C", fill=True)
    for d in DAYS_PDF:
        pdf.cell(day_w, 10, d, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_text_color(15, 23, 42)
    rendered = set()

    for slot in SLOTS_PDF:
        this_row_h = merged_row_h if slot["span"] == 2 else row_h
        pdf.set_x(10)

        # Time cell
        pdf.set_fill_color(241, 245, 249)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(time_w, this_row_h, slot["label"], border=1, align="C", fill=True)

        for day in DAYS_PDF:
            key = f"{day}-{slot['start']}"
            if key in rendered:
                continue

            cell_entries = [e for e in entries if e.day == day and e.start_time == slot["start"]]
            if slot["span"] == 2:
                mid = [e for e in entries if e.day == day and e.start_time == "12:15"]
                cell_entries = cell_entries + mid
                rendered.add(f"{day}-12:15")

            if not cell_entries:
                pdf.set_fill_color(255, 255, 255)
                pdf.set_text_color(200, 200, 200)
                pdf.set_font("Helvetica", "", 8)
                pdf.cell(day_w, this_row_h, "-", border=1, align="C", fill=True)
                pdf.set_text_color(15, 23, 42)
                continue

            first = cell_entries[0]
            c = courses.get(first.course_id)
            t = teachers.get(first.teacher_id)
            r = rooms.get(first.room_id)

            color = color_map.get(first.course_id, (219, 234, 254))

            code = (c.code if c else "?")[:14]
            name = (c.name if c else "?")[:20]
            tname = (t.name if t else "?")[:14]
            rname = (r.name if r else "?")[:10]

            x0 = pdf.get_x()
            y0 = pdf.get_y()

            pdf.set_fill_color(*color)
            pdf.rect(x0, y0, day_w, this_row_h, "F")

            pdf.set_xy(x0 + 1, y0 + 1)
            pdf.set_text_color(15, 23, 42)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(day_w - 2, 4, code, align="L")

            pdf.set_xy(x0 + 1, y0 + 5)
            pdf.set_font("Helvetica", "", 7)
            pdf.cell(day_w - 2, 4, name, align="L")

            pdf.set_xy(x0 + 1, y0 + 10)
            pdf.set_font("Helvetica", "", 6)
            pdf.cell(day_w - 2, 3, f"T: {tname}", align="L")

            pdf.set_xy(x0 + 1, y0 + 13)
            pdf.cell(day_w - 2, 3, f"R: {rname}", align="L")

            if slot["span"] == 2:
                pdf.set_xy(x0 + 1, y0 + 17)
                pdf.set_font("Helvetica", "I", 6)
                pdf.set_text_color(80, 80, 80)
                pdf.cell(day_w - 2, 3, "(2 hours)", align="L")
                pdf.set_text_color(15, 23, 42)

            pdf.set_xy(x0 + day_w, y0)

        pdf.ln(this_row_h)

    pdf.ln(4)
    pdf.set_text_color(100, 116, 139)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, f"Generated: {__import__('datetime').datetime.now().strftime('%d-%m-%Y %H:%M')}", ln=True, align="C")
    pdf.cell(0, 5, "Smart Timetable Management System", ln=True, align="C")

    raw = pdf.output(dest="S")
    if isinstance(raw, str):
        raw = raw.encode("latin-1", "ignore")
    elif isinstance(raw, bytearray):
        raw = bytes(raw)

    stream = BytesIO(bytes(raw))
    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=timetable_{user.username}.pdf"}
    )