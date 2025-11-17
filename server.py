"""
Mini Cloud Storage Backend
Developed by Rudra Pratap Singh
Powered by FastAPI + PostgreSQL + Fernet Encryption
"""

# ================================================================
# 1️⃣ IMPORTS
# ================================================================
import os
import psycopg2
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from cryptography.fernet import Fernet
import uvicorn
from models import Base
from database import engine

# Ensure models/tables created (SQLAlchemy)
Base.metadata.create_all(bind=engine)

# ================================================================
# 2️⃣ CONFIGURATION
# ================================================================
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL environment variable is not set!")

FRONTEND_URL = "https://rudravcloud.onrender.com"

KEY_FILE = "secret.key"
UPLOAD_DIR = "./chunks"
CHUNK_SIZE = 1024 * 1024  # 1 MB

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ================================================================
# 3️⃣ ENCRYPTION SETUP
# ================================================================
if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, "wb") as keyfile:
        keyfile.write(Fernet.generate_key())

with open(KEY_FILE, "rb") as keyfile:
    key = keyfile.read()

cipher = Fernet(key)

# ================================================================
# 4️⃣ DATABASE CONNECTION
# ================================================================
try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    print("Database connected successfully!")
except Exception as e:
    raise Exception(f"Database connection failed: {e}")

# ================================================================
# 5️⃣ FASTAPI INITIALIZATION
# ================================================================
app = FastAPI(title="Rudra Cloud API", version="1.0")
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================================================
# 6️⃣ ROUTES
# ================================================================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """
    Home page: fetch file list from DB and pass to template.
    Files will be a list of dicts: {"id": ..., "name": ...}
    """
    try:
        cursor.execute("SELECT id, filename FROM file_metadata ORDER BY uploaded_at DESC;")
        rows = cursor.fetchall()
        files = [{"id": r[0], "name": r[1]} for r in rows] if rows else []
    except Exception as e:
        print("Error in home():", e)
        files = []
    return templates.TemplateResponse("index.html", {"request": request, "files": files})


@app.get("/api/files", response_class=JSONResponse)
def list_files_api():
    try:
        cursor.execute("SELECT id, filename FROM file_metadata ORDER BY uploaded_at DESC;")
        rows = cursor.fetchall()

        files = [{"id": r[0], "name": r[1]} for r in rows] if rows else []
        return JSONResponse({"files": files})

    except Exception as e:
        print("Error in /api/files:", e)
        return JSONResponse({"files": []}, status_code=500)


@app.get("/health")
def health():
    return {"status": "running", "database_url": DATABASE_URL, "frontend": FRONTEND_URL}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), uploaded_by: str = "user1"):
    try:
        temp_path = os.path.join(UPLOAD_DIR, file.filename)
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        # Insert metadata into file_metadata
        cursor.execute(
            """
            INSERT INTO file_metadata (filename, chunks_count, chunk_size, uploaded_by)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (file.filename, 0, CHUNK_SIZE, uploaded_by)
        )
        file_id = cursor.fetchone()[0]

        # Encrypt and split into chunks
        chunks_count = 0
        with open(temp_path, "rb") as f:
            index = 0
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                encrypted_chunk = cipher.encrypt(chunk)
                # NOTE: your repo uses filename + "chunk" + index (no underscore)
                chunk_path = os.path.join(UPLOAD_DIR, f"{file.filename}chunk{index}")
                with open(chunk_path, "wb") as cf:
                    cf.write(encrypted_chunk)
                # Insert chunk metadata
                cursor.execute(
                    """
                    INSERT INTO chunk_metadata (file_id, chunk_index, lender_node)
                    VALUES (%s, %s, %s)
                    """,
                    (file_id, index, "node1")
                )
                index += 1
                chunks_count += 1

        # Update chunks count in file_metadata
        cursor.execute(
            "UPDATE file_metadata SET chunks_count=%s WHERE id=%s",
            (chunks_count, file_id)
        )

        os.remove(temp_path)

        return JSONResponse(content={"status": "success", "file_id": file_id, "chunks": chunks_count})

    except Exception as e:
        print("Error in upload_file:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload_chunk/")
async def upload_chunk(file: UploadFile = File(...), uploaded_by: str = "user1"):
    print("Alias route called for:", file.filename)
    try:
        return await upload_file(file, uploaded_by)
    except Exception as e:
        print("Error in upload_chunk:", e)
        raise

@app.get("/download_by_name/{filename}")
def download_by_name(filename: str):
    try:
        cursor.execute("SELECT id FROM file_metadata WHERE filename=%s", (filename,))
        r = cursor.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="File not found")
        return download_file(r[0])  # reuse existing function
    except HTTPException:
        raise
    except Exception as e:
        print("Error in download_by_name:", e)
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/download/{file_id}")
def download_file(file_id: int):
    try:
        cursor.execute(
            "SELECT filename, chunks_count FROM file_metadata WHERE id=%s",
            (file_id,)
        )
        file_meta = cursor.fetchone()
        if not file_meta:
            raise HTTPException(status_code=404, detail="File not found")

        filename, chunks_count = file_meta

        def iter_decrypted():
            for i in range(chunks_count):
                # use same naming as upload: filename + "chunk" + index
                chunk_path = os.path.join(UPLOAD_DIR, f"{filename}chunk{i}")
                if not os.path.exists(chunk_path):
                    # raise inside generator so StreamingResponse exposes error
                    raise HTTPException(status_code=404, detail=f"Chunk {i} missing")
                with open(chunk_path, "rb") as cf:
                    enc = cf.read()
                try:
                    dec = cipher.decrypt(enc)
                except Exception as ex:
                    print(f"Decrypt error for chunk {i}:", ex)
                    raise HTTPException(status_code=500, detail="Decryption failed")
                yield dec

        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(iter_decrypted(), media_type="application/octet-stream", headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        print("Error in download_file:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download_chunk/{file_id}")
def download_chunk(file_id: int):
    return download_file(file_id)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
