# 📅 Smart Timetable Management System

A full-stack web application for automatic college timetable generation using constraint-based scheduling.

## 🚀 Features

- 🔐 **Multi-user authentication** (admin, teacher, student)
- 👨‍🏫 **Teacher management** (internal + external faculty)
- 📚 **Course management** with department & class
- 🏫 **Room management** (classrooms + labs)
- ⚡ **CSP-based auto timetable generation**
- 🔄 **Manual slot change** with conflict detection
- 🌐 **REST API** with JWT authentication

## 🛠 Tech Stack

- **Frontend:** HTML5, CSS3, Vanilla JavaScript *(Day 8)*
- **Backend:** Python 3.12, FastAPI, SQLAlchemy
- **Database:** SQLite
- **Auth:** JWT (python-jose, bcrypt)

## 📦 Installation

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
