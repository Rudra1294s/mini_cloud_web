import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import psycopg2
from cryptography.fernet import Fernet

# ----------------------
# Configuration
# ----------------------
UPLOAD_DIR = "./chunks"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Encryption key (store securely in production)
key = Fernet.generate_key()
cipher = Fernet(key)

# PostgreSQL connection
conn = psycopg2.connect(
    dbname="cloud_db",
    user="postgres",
    password="password",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory="templates")

CHUNK_SIZE = 1024 * 1024  # 1 MB

# ----------------------
# HTML Homepage
# ----------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ----------------------
# File Upload API
# ----------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...), uploaded_by: str = "user1"):
    try:
        # Save full file temporarily
        temp_path = os.path.join(UPLOAD_DIR, file.filename)
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        # Save file metadata first
        cursor.execute(
            "INSERT INTO file_metadata (filename, chunks_count, chunk_size, uploaded_by) VALUES (%s, %s, %s, %s) RETURNING id",
            (file.filename, 0, CHUNK_SIZE, uploaded_by)
        )
        file_id = cursor.fetchone()[0]
        conn.commit()

        # Chunk & encrypt
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

                # Save chunk metadata
                cursor.execute(
                    "INSERT INTO chunk_metadata (file_id, chunk_index, lender_node) VALUES (%s, %s, %s)",
                    (file_id, index, "node1")  # Replace node1 with real device later
                )
                index += 1
                chunks_count += 1

        # Update chunks_count in file_metadata
        cursor.execute("UPDATE file_metadata SET chunks_count=%s WHERE id=%s", (chunks_count, file_id))
        conn.commit()

        # Remove temp full file
        os.remove(temp_path)

        return JSONResponse(content={"status": "success", "file_id": file_id, "chunks": chunks_count})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------
# File Download API
# ----------------------
@app.get("/download/{file_id}")
def download_file(file_id: int):
    try:
        # Fetch file metadata
        cursor.execute("SELECT filename, chunks_count FROM file_metadata WHERE id=%s", (file_id,))
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

        return FileResponse(path=merged_path, filename=filename, media_type='application/octet-stream')

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
