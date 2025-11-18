import os
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Videorequest, Videojob, Upload as UploadSchema

app = FastAPI(title="VideoGen AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "VideoGen AI Backend running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# -----------------------------
# File Upload Endpoints
# -----------------------------
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), type: str = Form("reference")):
    if type not in ("reference", "image2video"):
        raise HTTPException(status_code=400, detail="Invalid type")
    # In this environment we don't persist binary files to disk; we simulate a storage URL
    content = await file.read()
    size = len(content)
    doc = UploadSchema(
        filename=file.filename,
        url=f"/uploads/{file.filename}",
        type=type,
        size=size,
        content_type=file.content_type or "application/octet-stream",
    )
    new_id = create_document("upload", doc)
    return {"id": new_id, "url": doc.url, "filename": doc.filename, "size": size, "type": type}

@app.get("/api/uploads")
def list_uploads():
    items = get_documents("upload")
    # Convert ObjectId to string
    for it in items:
        if isinstance(it.get("_id"), ObjectId):
            it["id"] = str(it.pop("_id"))
    return items

# -----------------------------
# Video Generation (Simulated)
# -----------------------------
class GenerateRequest(BaseModel):
    prompt: str
    duration: int
    style: str
    aspect_ratio: str
    variations: int = 1
    reference_image_ids: List[str] = []
    image_to_video_ids: List[str] = []

@app.post("/api/generate")
def generate_videos(req: GenerateRequest):
    # Persist the original request
    vr = Videorequest(**req.model_dump())
    req_id = create_document("videorequest", vr)

    jobs = []
    for i in range(req.variations):
        job = Videojob(
            prompt=req.prompt,
            duration=vr.duration,
            style=vr.style,
            aspect_ratio=vr.aspect_ratio,
            reference_image_ids=vr.reference_image_ids,
            image_to_video_ids=vr.image_to_video_ids,
            variation_index=i,
            status="completed",
            video_url=f"https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"
        )
        job_id = create_document("videojob", job)
        jobs.append({"id": job_id, **job.model_dump()})

    return {"request_id": req_id, "jobs": jobs}

@app.get("/api/history")
def history(limit: int = 25):
    docs = get_documents("videorequest", limit=limit)
    for d in docs:
        if isinstance(d.get("_id"), ObjectId):
            d["id"] = str(d.pop("_id"))
    # Sort by created_at desc if present
    try:
        docs.sort(key=lambda x: x.get("created_at"), reverse=True)
    except Exception:
        pass
    return docs

@app.get("/api/jobs")
def list_jobs(limit: int = 50):
    docs = get_documents("videojob", limit=limit)
    for d in docs:
        if isinstance(d.get("_id"), ObjectId):
            d["id"] = str(d.pop("_id"))
    try:
        docs.sort(key=lambda x: x.get("created_at"), reverse=True)
    except Exception:
        pass
    return docs

class SaveRequest(BaseModel):
    job_id: str
    saved: bool

@app.post("/api/save")
def save_job(req: SaveRequest):
    from bson import ObjectId
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        res = db.videojob.update_one({"_id": ObjectId(req.job_id)}, {"$set": {"saved": req.saved, "updated_at": __import__('datetime').datetime.utcnow()}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"status": "ok", "updated": res.modified_count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
