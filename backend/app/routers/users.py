from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/users", tags=["users"])


def verify_admin_password(int_password: int, db: Session) -> bool:
    """Check if int_password matches ANY admin's password"""
    admin = db.query(models.User).filter(
        models.User.role == "admin",
        models.User.int_password == int_password
    ).first()
    return admin is not None


@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check username/email
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(400, "Username already exists")
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(400, "Email already exists")

    # For admin: password must be unique among admins
    if user.role == "admin":
        existing = db.query(models.User).filter(
            models.User.role == "admin",
            models.User.int_password == user.int_password
        ).first()
        if existing:
            raise HTTPException(400, "Admin password already in use. Choose a different number.")
    else:
        # For teacher/student: password must match SOME admin
        if not verify_admin_password(user.int_password, db):
            raise HTTPException(400, "Invalid admin password")

    # Validate student fields
    if user.role == "student":
        if not all([user.department, user.semester, user.division, user.batch]):
            raise HTTPException(400, "Department, semester, division, batch required for students")

    new_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=auth.hash_password(user.password),
        role=user.role,
        int_password=user.int_password,
        department=user.department,
        semester=user.semester,
        division=user.division,
        batch=user.batch
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login")
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == credentials.username).first()

    if not user or not auth.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Verify int_password
    if user.int_password != credentials.int_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin password"
        )

    token = auth.create_access_token(data={"sub": user.username, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "department": user.department,
            "semester": user.semester,
            "division": user.division,
            "batch": user.batch
        }
    }


@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@router.get("/admins", response_model=list[schemas.UserResponse])
def get_admins(db: Session = Depends(get_db),
               user: models.User = Depends(auth.get_current_admin)):
    """List all admins (for internal use)"""
    return db.query(models.User).filter(models.User.role == "admin").all()