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

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


# Load activities from JSON file
import json
ACTIVITIES_FILE = os.path.join(current_dir, "activities.json")
def load_activities():
    with open(ACTIVITIES_FILE, "r") as f:
        return json.load(f)

def save_activities(activities):
    with open(ACTIVITIES_FILE, "w") as f:
        json.dump(activities, f, indent=2, ensure_ascii=False)


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")



@app.get("/activities")
def get_activities():
    return load_activities()



@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, slot_index: int = 0):
    """Sign up a student for an activity slot"""
    activities = load_activities()
    for activity in activities:
        if activity["name"] == activity_name:
            if slot_index < 0 or slot_index >= len(activity["slots"]):
                raise HTTPException(status_code=400, detail="Invalid slot index")
            slot = activity["slots"][slot_index]
            if email in slot["participants"]:
                raise HTTPException(status_code=400, detail="Student is already signed up for this slot")
            if len(slot["participants"]) >= slot["max_participants"]:
                raise HTTPException(status_code=400, detail="Slot is full")
            slot["participants"].append(email)
            save_activities(activities)
            return {"message": f"Signed up {email} for {activity_name} ({slot['time']})"}
    raise HTTPException(status_code=404, detail="Activity not found")



@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, slot_index: int = 0):
    """Unregister a student from an activity slot"""
    activities = load_activities()
    for activity in activities:
        if activity["name"] == activity_name:
            if slot_index < 0 or slot_index >= len(activity["slots"]):
                raise HTTPException(status_code=400, detail="Invalid slot index")
            slot = activity["slots"][slot_index]
            if email not in slot["participants"]:
                raise HTTPException(status_code=400, detail="Student is not signed up for this slot")
            slot["participants"].remove(email)
            save_activities(activities)
            return {"message": f"Unregistered {email} from {activity_name} ({slot['time']})"}
    raise HTTPException(status_code=404, detail="Activity not found")

# 自動分配學生到多活動多時段
import random
@app.post("/auto-assign")
def auto_assign(students: list[str]):
    """自動將學生分配到所有活動的所有時段，盡量均勻分配"""
    activities = load_activities()
    assignments = {s: [] for s in students}
    # 將學生隨機排序
    random.shuffle(students)
    # 依序分配到每個活動的每個時段
    for activity in activities:
        for slot in activity["slots"]:
            slot["participants"] = []
    idx = 0
    total_slots = sum(len(a["slots"]) for a in activities)
    for i, student in enumerate(students):
        # 輪流分配到不同活動與時段
        slot_num = i % total_slots
        count = 0
        for activity in activities:
            for slot in activity["slots"]:
                if count == slot_num:
                    if len(slot["participants"]) < slot["max_participants"]:
                        slot["participants"].append(student)
                        assignments[student].append({"activity": activity["name"], "slot": slot["time"]})
                    break
                count += 1
            if count > slot_num:
                break
    save_activities(activities)
    return {"assignments": assignments}
