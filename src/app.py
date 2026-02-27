"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""


from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
import sqlite3

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# SQLite setup
DB_PATH = os.path.join(current_dir, "activities.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# Create tables if not exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS activities (
    name TEXT PRIMARY KEY,
    description TEXT,
    schedule TEXT,
    max_participants INTEGER
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS participants (
    activity_name TEXT,
    email TEXT,
    PRIMARY KEY (activity_name, email),
    FOREIGN KEY (activity_name) REFERENCES activities(name)
)
""")
conn.commit()

# Seed initial activities if table is empty
def seed_activities():
    cursor.execute("SELECT COUNT(*) FROM activities")
    if cursor.fetchone()[0] == 0:
        initial = [
            ("Chess Club", "Learn strategies and compete in chess tournaments", "Fridays, 3:30 PM - 5:00 PM", 12),
            ("Programming Class", "Learn programming fundamentals and build software projects", "Tuesdays and Thursdays, 3:30 PM - 4:30 PM", 20),
            ("Gym Class", "Physical education and sports activities", "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM", 30),
            ("Soccer Team", "Join the school soccer team and compete in matches", "Tuesdays and Thursdays, 4:00 PM - 5:30 PM", 22),
            ("Basketball Team", "Practice and play basketball with the school team", "Wednesdays and Fridays, 3:30 PM - 5:00 PM", 15),
            ("Art Club", "Explore your creativity through painting and drawing", "Thursdays, 3:30 PM - 5:00 PM", 15),
            ("Drama Club", "Act, direct, and produce plays and performances", "Mondays and Wednesdays, 4:00 PM - 5:30 PM", 20),
            ("Math Club", "Solve challenging problems and participate in math competitions", "Tuesdays, 3:30 PM - 4:30 PM", 10),
            ("Debate Team", "Develop public speaking and argumentation skills", "Fridays, 4:00 PM - 5:30 PM", 12)
        ]
        cursor.executemany("INSERT INTO activities VALUES (?, ?, ?, ?)", initial)
        conn.commit()
seed_activities()



@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")

@app.get("/activities")
def get_activities():
    cursor.execute("SELECT * FROM activities")
    rows = cursor.fetchall()
    result = {}
    for name, description, schedule, max_participants in rows:
        cursor.execute("SELECT email FROM participants WHERE activity_name=?", (name,))
        participants = [row[0] for row in cursor.fetchall()]
        result[name] = {
            "description": description,
            "schedule": schedule,
            "max_participants": max_participants,
            "participants": participants
        }
    return result

@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    # Validate activity exists
    cursor.execute("SELECT max_participants FROM activities WHERE name=?", (activity_name,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Check if already signed up
    cursor.execute("SELECT 1 FROM participants WHERE activity_name=? AND email=?", (activity_name, email))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Student is already signed up")

    # Check if activity is full
    cursor.execute("SELECT COUNT(*) FROM participants WHERE activity_name=?", (activity_name,))
    count = cursor.fetchone()[0]
    if count >= row[0]:
        raise HTTPException(status_code=400, detail="Activity is full")

    cursor.execute("INSERT INTO participants VALUES (?, ?)", (activity_name, email))
    conn.commit()
    return {"message": f"Signed up {email} for {activity_name}"}

@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    # Validate activity exists
    cursor.execute("SELECT 1 FROM activities WHERE name=?", (activity_name,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is signed up
    cursor.execute("SELECT 1 FROM participants WHERE activity_name=? AND email=?", (activity_name, email))
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    cursor.execute("DELETE FROM participants WHERE activity_name=? AND email=?", (activity_name, email))
    conn.commit()
    return {"message": f"Unregistered {email} from {activity_name}"}
