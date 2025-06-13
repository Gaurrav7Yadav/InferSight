import os
import tempfile
import shutil

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

# Import your process_document function
from extract_fields import process_document

router = APIRouter()

@router.post(
    "/", 
    status_code=status.HTTP_200_OK, 
    summary="Perform KIE via OCR + LLM",
    response_model=list[dict]  # returning a list of clean-field dicts
)
async def perform_kie(files: list[UploadFile] = File(...)):  
    """
    1) Save each uploaded file to a temporary path
    2) Call process_document() on it
    3) Collect the cleaned field dict and return it
    """
    results = []

    for upload in files:
        # 1️⃣ Save upload to a temp file
        ext = os.path.splitext(upload.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            content = await upload.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # 2️⃣ Run your OCR + LLM extraction
            clean_fields = process_document(tmp_path)
            results.append({
                "filename": upload.filename,
                "fields": clean_fields
            })
        except Exception as e:
            # If extraction fails, return a 500 with error detail
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            # 3️⃣ Clean up the temp file
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    # 4️⃣ Return list of { filename, fields } objects
    return JSONResponse(content=results)
