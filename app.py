from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import shutil
from extract_fields import process_document  # <- we'll wrap your logic

app = FastAPI()

# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploaded_docs"

@app.post("/extract-fields")
async def extract_fields(file: UploadFile = File(...)):
    # Save uploaded file
    file_ext = os.path.splitext(file.filename)[1]
    saved_path = os.path.join(UPLOAD_FOLDER, f"uploaded{file_ext}")
    
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run your field extraction
    try:
        result = process_document(saved_path)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
