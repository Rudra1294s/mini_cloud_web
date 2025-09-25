import uvicorn
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import os

# FastAPI app
app = FastAPI()

# Enable CORS for all origins (Web + Flutter friendly)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all domains
    allow_methods=["*"],  # allow GET, POST, etc.
    allow_headers=["*"],
)

# Folder for uploaded files
UPLOAD_FOLDER = "uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Jinja2 templates
templates = Jinja2Templates(directory="templates")

# ----------------------
# Root route (home page)
# ----------------------
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    try:
        all_files = os.listdir(UPLOAD_FOLDER)
        files = [f for f in all_files if not f.startswith('.')]
        return templates.TemplateResponse("index.html", {"request": request, "files": files})
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "files": [], "error": str(e)})

# ----------------------
# Upload file (POST)
# ----------------------
@app.post("/upload_chunk/")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        return {"status": "success"}
    except Exception as e:
        return {"status": f"failed: {e}"}

# ----------------------
# Download file (GET)
# ----------------------
@app.get("/download_chunk/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/octet-stream', filename=filename)
    return {"status": "file not found"}

# ----------------------
# Recent files (API)
# ----------------------
@app.get("/recent_files/")
async def recent_files():
    try:
        all_files = os.listdir(UPLOAD_FOLDER)
        files = [f for f in all_files if not f.startswith('.')]
        return JSONResponse(content={"files": files}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"files": [], "error": str(e)}, status_code=500)

# ----------------------
# Run server
# ----------------------
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)
