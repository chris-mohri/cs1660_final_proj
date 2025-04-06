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



