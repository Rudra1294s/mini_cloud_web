import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os

# FastAPI app
app = FastAPI()

# Enable CORS for all origins (Web-friendly)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all domains
    allow_methods=["*"],  # allow GET, POST, etc.
    allow_headers=["*"],
)

# Folder for uploaded files
CHUNK_DIR = Path("chunks")
CHUNK_DIR.mkdir(exist_ok=True)

# Upload file (POST)
@app.post("/upload_chunk/")
async def upload_chunk(file: UploadFile = File(...)):
    file_path = CHUNK_DIR / file.filename
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"status": "uploaded", "filename": file.filename}

# Download file (GET)
@app.get("/download_chunk/{filename}")
async def download_chunk(filename: str):
    file_path = CHUNK_DIR / filename
    if file_path.exists():
        return FileResponse(
            path=file_path,
            media_type="application/octet-stream",
            filename=filename
        )
    return {"status": "not_found"}

if _name_ == "_main_":
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)