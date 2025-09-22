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
async def upload_file(file: UploadFile = File(...)):
    try:
        file_path = os.path.join("uploaded_files", file.filename)
        os.makedirs("uploaded_files", exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        return {"status": "success"}
    except Exception as e:
        return {"status": f"failed: {e}"}

# Download file (GET)
@app.get("/download_chunk/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/octet-stream', filename=filename)
    return {"status": "file not found"}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)