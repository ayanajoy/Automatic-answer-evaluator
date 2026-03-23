import os
from pdf2image import convert_from_path
import easyocr
import tempfile
import numpy as np

# Initialize the EasyOCR reader (loads models into memory)
# Using 'en' for English characters
reader = easyocr.Reader(['en'])

import cv2

def extract_text_from_image(img_input) -> str:
    """
    Extracts text from a single image (numpy array or path) with OpenCV preprocessing.
    """
    if isinstance(img_input, str):
        img = cv2.imread(img_input)
    else:
        # Assuming numpy array from buffer
        img = img_input

    # 1. Convert to grayscale
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
        
    # 2. Apply a subtle Gaussian blur to remove high-frequency noise
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 3. Adaptive Thresholding to make text pop out purely black-and-white
    # This specifically helps poorly lit photos or light handwriting strokes outshine the background
    thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Note: paragraph=True helps bundle text lines that belong together, preventing disjointed sentences.
    results = reader.readtext(thresh, detail=0, paragraph=True)
    return "\n".join(results)

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Attempts to extract digital text using pdfplumber first.
    If the PDF is a scanned image, falls back to EasyOCR (requires Poppler).
    """
    extracted_text = ""
    
    # 1. Try digital text extraction first (no Poppler needed)
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
        
        if extracted_text.strip():
            return extracted_text.strip()
    except Exception as e:
        print(f"pdfplumber extraction failed: {e}")

    # 2. Fallback to OCR (Requires Poppler)
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(
    pdf_path,
    poppler_path=r"C:\poppler-25.12.0\Library\bin"
)
    except Exception as e:
        print(f"Error converting PDF to images (ensure Poppler is installed): {e}")
        return ""

    for i, img in enumerate(images):
        print(f"Processing page {i+1}...")
        
        # Convert PIL Image to numpy array format which EasyOCR expects
        img_np = np.array(img)
        page_text = extract_text_from_image(img_np)
        extracted_text += page_text + "\n"
        
    return extracted_text.strip()