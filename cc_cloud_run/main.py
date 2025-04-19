import base64
import io
from pathlib import Path
import re
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google.cloud import firestore
from typing import Annotated
from .database import Base, QRCode, get_engine
from sqlalchemy.orm import sessionmaker
import datetime
from google.cloud import recaptchaenterprise_v1
from google.cloud.recaptchaenterprise_v1 import Assessment

app = FastAPI()
engine = get_engine()
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


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

    try:
        image_bytes = base64.b64decode(image_data)
    except Exception as e:
        print("error decoding image: ", e)
        raise HTTPException(status_code=400, detail="Invalid image encoding")

    db = SessionLocal()
    try:
        qr_entry = QRCode(qrcode=image_bytes)
        print("commiting to db")
        db.add(qr_entry)
        
        db.commit()
        db.refresh(qr_entry)
        return {"id": qr_entry.id, "date": qr_entry.date.isoformat()}
    finally:
        db.close()


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

@app.get("/past-attendance")
async def past_attendance(request: Request):
    db = SessionLocal()
    try:
        qrcodes = db.query(QRCode).all()
        qrcode_data = []
        for qrcode in qrcodes:
            base64_qr = base64.b64encode(qrcode.qrcode).decode('utf-8')
            qrcode_data.append({
                "id": qrcode.id,
                "date": qrcode.date,
                "image": f"data:image/png;base64,{base64_qr}"
            })
        return templates.TemplateResponse("past-attendance.html", {"request": request, "qrcodes" :qrcode_data})
    finally:
        db.close()

@app.get("/download-qr/{qr_id}")
async def download_qr(qr_id: int):
    db = SessionLocal()
    try: 
        qr = db.query(QRCode).filter(QRCode.id == qr_id).first()
        if not qr:
            raise HTTPException(status_code=404, detail="QR code not found")
        return StreamingResponse(
            io.BytesIO(qr.qrcode),
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=qr_{qr_id}.png"}
        )
    finally:
        db.close()

def create_assessment(project_id: str, recaptcha_key: str, token: str, recaptcha_action: str) -> Assessment:
    
    client = recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient

    event = recaptchaenterprise_v1.Event()
    event.site_key = recaptcha_key
    event.token = token

    assessment = recaptchaenterprise_v1.Assessment()
    assessment.event = event

    request = recaptchaenterprise_v1.CreateAssessmentRequest()
    request.assessment = assessment
    request.parent = f"projects/{project_id}"

    response = client.create_assessment(request)

    if not response.token_properties.valid:
        print("Invalid token", response.token_properties.invalid_reason)
        raise HTTPException(status_code=400, detail="Invalid reCaptcha Token")
    
    if response.token_properties.action != recaptcha_action:
        print("Action.")
        raise HTTPException(status_code=400, detail="Invalid reCaptcha Token")
    
    print("Score: ", response.risk_analysis.score)
    for reason in response.risk_analysis.reasons:
            print("Reason:", reason)

    return response

@app.post("/verify-recaptcha")
async def verify_recaptcha(request: Request):
    data = await request.json()
    token = data.get("token")
    action = data.get("action", "login")

    if not token:
        raise HTTPException(status_code=400, detail="no reCaptcha token provided")
    
    assessment = create_assessment(
        project_id="strawhattendance",
        recaptcha_key="6LeM5BwrAAAAACiRMi7fyG_43Qu6Mp6Xeh3saNkZ",
        token=token,
        recaptcha_action=action
    )

    return {
        "score": assessment.risk_analysis.score,
        "reasons": [str(r) for r in assessment.risk_analysis.reasons]
    }

