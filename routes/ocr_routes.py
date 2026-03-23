from fastapi import APIRouter, UploadFile, File
import shutil
from ocr import extract_text_from_pdf

router = APIRouter()

@router.post("/ocr")
async def perform_ocr(file: UploadFile = File(...)):

    file_location = f"uploads/{file.filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extracted_text = extract_text_from_pdf(file_location)

    return {
        "extracted_text": extracted_text
    }