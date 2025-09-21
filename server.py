import uvicorn 
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors
import CORSMiddleware
from pathlib import Path
import os


# FastAPI app
app = FastAPI()

# ===== CORS Middleware =====
# Allow Flutter Web to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[""],       # "" means all domains
    allow_methods=["*"],       # GET, POST, etc.
    allow_headers=["*"]
)
# Chunks folder path
CHUNK_DIR = Path("chunks")
CHUNK_DIR.mkdir(exist_ok=True)

# Templates folder path
templates = Jinja2Templates(directory="templates")

# Home page
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    files = os.listdir(CHUNK_DIR)
    return templates.TemplateResponse("index.html", {"request": request, "files": files})

# Upload file
@app.post("/upload_chunk/")
async def upload_chunk(file: UploadFile = File(...)):
    file_path = CHUNK_DIR / file.filename
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"status": "uploaded", "filename": file.filename}

# Download file
@app.get("/download_chunk/{filename}")
async def download_chunk(filename: str):
    file_path = CHUNK_DIR / filename
    if file_path.exists():
        return FileResponse(
            path=file_path,
            media_type="application/octet-stream",  # force download
            filename=filename  # download file with original name
        )
    return {"status": "not_found"}
# import uvicorn

if __name__ == "__main__": uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)