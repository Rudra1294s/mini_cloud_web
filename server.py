"""
Mini Cloud Storage Backend
Developed by Rudra Pratap Singh
Powered by FastAPI + PostgreSQL + Fernet Encryption
"""

import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from cryptography.fernet import Fernet

# ================================================================
# 🔧 CONFIGURATION (Rudra’s Cloud Setup)
# ================================================================
DB_NAME = "cloud_db"
DB_USER = "postgres"
DB_PASSWORD = "kali1294$"
DB_HOST = "localhost"
DB_PORT = "5432"

# Frontend URL (for CORS)
FRONTEND_URL = "https://rudravcloud.onrender.com"

# Encryption key file (persistent)
KEY_FILE = "secret.key"

# Upload storage directory
UPLOAD_DIR = "./chunks"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# ================================================================
# 🔐 ENCRYPTION SETUP
# ================================================================
if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, "wb") as keyfile:
        keyfile.write(Fernet.generate_key())

with open(KEY_FILE, "rb") as keyfile:
    key = keyfile.read()

cipher = Fernet(key)

# ================================================================
# 🗄️ DATABASE CONNECTION
# ================================================================
try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()
    print("✅ Database connected successfully!")
except Exception as e:
    raise Exception(f"❌ Database connection failed: {e}")

# ================================================================
# 🚀 FASTAPI INITIALIZATION
# ================================================================
app = FastAPI(title="Rudra Cloud API", version="1.0")
templates = Jinja2Templates(directory="templates")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CHUNK_SIZE = 1024 * 1024  # 1 MB

# ================================================================
# 🌐 ROUTES
# ================================================================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Serves homepage (index.html)"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "running",
        "database": DB_NAME,
        "frontend": FRONTEND_URL
    }


# ------------------------------------------------
# 📤 File Upload API
# ------------------------------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...), uploaded_by: str = "user1"):
    try:
        temp_path = os.path.join(UPLOAD_DIR, file.filename)
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        # Insert metadata
        cursor.execute(
            """
            INSERT INTO file_metadata (filename, chunks_count, chunk_size, uploaded_by)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (file.filename, 0, CHUNK_SIZE, uploaded_by)
        )
        file_id = cursor.fetchone()[0]
        conn.commit()

        # Encrypt + split file into chunks
        chunks_count = 0
        with open(temp_path, "rb") as f:
            index = 0
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break

                encrypted_chunk = cipher.encrypt(chunk)
                chunk_path = os.path.join(UPLOAD_DIR, f"{file.filename}_chunk_{index}")

                with open(chunk_path, "wb") as cf:
                    cf.write(encrypted_chunk)

                cursor.execute(
                    """
                    INSERT INTO chunk_metadata (file_id, chunk_index, lender_node)
                    VALUES (%s, %s, %s)
                    """,
                    (file_id, index, "node1")
                )
                index += 1
                chunks_count += 1

        cursor.execute(
            "UPDATE file_metadata SET chunks_count=%s WHERE id=%s",
            (chunks_count, file_id)
        )
        conn.commit()

        os.remove(temp_path)

        return JSONResponse(
            content={
                "status": "success",
                "file_id": file_id,
                "chunks": chunks_count
            }
        )

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------
# 📥 File Download API
# ------------------------------------------------
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
        merged_path = os.path.join(UPLOAD_DIR, f"downloaded_{filename}")

        with open(merged_path, "wb") as merged_file:
            for i in range(chunks_count):
                chunk_path = os.path.join(UPLOAD_DIR, f"{filename}_chunk_{i}")
                if not os.path.exists(chunk_path):
                    raise HTTPException(status_code=404, detail=f"Chunk {i} missing")

                with open(chunk_path, "rb") as cf:
                    encrypted_chunk = cf.read()
                    decrypted_chunk = cipher.decrypt(encrypted_chunk)
                    merged_file.write(decrypted_chunk)

        response = FileResponse(
            path=merged_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(merged_path):
            os.remove(merged_path)
