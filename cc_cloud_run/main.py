import base64
from pathlib import Path
import re
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google.cloud import firestore
from typing import Annotated
import datetime

app = FastAPI()

# mount static files
app.mount("/static", StaticFiles(directory="/app/static"), name="static")
templates = Jinja2Templates(directory="/app/template")

# init firestore client
db = firestore.Client()
votes_collection = db.collection("votes")

# NEW
attendance_collection = db.collection("attendance")

@app.get("/")
async def read_root(request: Request):
    tabsCount=0
    spacesCount=0
    votes = votes_collection.stream()
    vote_data = []

    for v in votes:
        newDoc = v.to_dict()
        vote_data.append(newDoc)

        if (newDoc["team"]=="TABS"):
            tabsCount+=1
        else:
            spacesCount+=1

    return templates.TemplateResponse("index.html", {
        "request": request,
        "tabs_count": tabsCount,
        "spaces_count": spacesCount,
        "recent_votes": vote_data
    })


@app.post("/")
async def create_vote(team: Annotated[str, Form()]):
    if team not in ["TABS", "SPACES"]:
        raise HTTPException(status_code=400, detail="Invalid vote")

    votes_collection.add({
    "team": team,
    "time_cast": datetime.datetime.now(datetime.timezone.utc).isoformat()
    })

# db.collection("cities").document("LA").set(data)

@app.post("/reset_attendance")
async def reset_attendance():
    print("attempt to clear attendance")
    docs = attendance_collection.stream()
    for doc in docs:
        if (doc.id!="dummy"):
            attendance_collection.document(doc.id).delete()


@app.post("/upload-image")
async def upload_image(request: Request):
    data = await request.json()
    image_data = data["image"]

@app.post("/add_student")
# only adds if student email is not already present in collection
async def addStudent(name: Annotated[str, Form()], email: Annotated[str, Form()], key: Annotated[str, Form()]):
    toAdd = True

    docs = attendance_collection.stream()
    for doc in docs:
        if doc.get("email")==email:
            toAdd=False
            break
    
    if (toAdd):
        attendance_collection.add({
        "name": name,
        "email":email,
        "key":key
        })

@app.get("/update_html")
async def updateHTML():
    attendance = attendance_collection.stream()
    attendance_data = []

    for a in attendance:
        newDoc = a.to_dict()
        attendance_data.append([newDoc["name"], newDoc["email"], newDoc["key"]])

    return attendance_data

