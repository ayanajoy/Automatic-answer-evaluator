import os
import tempfile
import numpy as np
import cv2

# OCR Engine Initializers
ocr_paddle = None
ocr_easy = None

# 1. Try PaddleOCR first
try:
    from paddleocr import PaddleOCR
    ocr_paddle = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
except ImportError:
    print("Warning: PaddleOCR not installed. Attempting EasyOCR fallback...")

# 2. Try EasyOCR second
try:
    import easyocr
    ocr_easy = easyocr.Reader(['en'], gpu=False) # GPU=False for better compatibility in CPU environments
except ImportError:
    print("Error: Neither PaddleOCR nor EasyOCR are installed.")


def extract_text_from_image(img_input) -> str:
    """
    Extracts text from a single image using PaddleOCR (preferred) or EasyOCR (fallback).
    """
    if ocr_paddle is None and ocr_easy is None:
        return "Error: No OCR engine installed"

    if isinstance(img_input, str):
        img = cv2.imread(img_input)
    else:
        img = img_input

    # Try PaddleOCR
    if ocr_paddle:
        try:
            results = ocr_paddle.ocr(img, cls=True)
            extracted_text = []
            if results and results[0]:
                for line in results[0]:
                    text = line[1][0]
                    extracted_text.append(text)
                return "\n".join(extracted_text)
        except Exception as e:
            print(f"PaddleOCR error: {e}. Falling back to EasyOCR...")

    # Fallback to EasyOCR
    if ocr_easy:
        try:
            # EasyOCR expects a filepath or numpy array
            results = ocr_easy.readtext(img)
            # result structure: ([[x,y],[x,y],[x,y],[x,y]], "text", 0.99)
            extracted_text = [res[1] for res in results]
            return "\n".join(extracted_text)
        except Exception as e:
            return f"Error: OCR failed. {e}"

    return "Error: All OCR engines failed"

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Attempts to extract digital text using pdfplumber first.
    If the PDF is a scanned image, falls back to PaddleOCR (requires Poppler).
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

    # 2. Fallback to PaddleOCR (Requires Poppler)
    try:
        from pdf2image import convert_from_path
        import shutil

        # Check if pdftoppm is in PATH or try common locations
        poppler_bin = None
        if shutil.which("pdftoppm"):
            poppler_bin = None # It's in system PATH
        else:
            # Check a few common dev paths just in case, but don't crash if missing
            potential_paths = [
                r"C:\poppler\bin",
                r"C:\Program Files\poppler\bin",
                r"C:\Users\HP\poppler\Library\bin" # Example user path
            ]
            for p in potential_paths:
                if os.path.exists(os.path.join(p, "pdftoppm.exe")):
                    poppler_bin = p
                    break
        
        images = convert_from_path(
            pdf_path,
            poppler_path=poppler_bin
        )
    except Exception as e:
        print(f"!!! OCR ERROR: PDF-to-Image conversion failed. !!!")
        print(f"Reason: {e}")
        print("Note: To process scanned PDFs, you must install Poppler.")
        print("Download from: https://github.com/oschwartz10612/poppler-windows/releases")
        return ""

    for i, img in enumerate(images):
        print(f"Processing page {i+1}...")
        
        # Convert PIL Image to numpy array format which PaddleOCR expects
        # Convert RGB (PIL) to BGR (OpenCV) just in case, though PaddleOCR handles RGB
        img_np = np.array(img)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        
        page_text = extract_text_from_image(img_bgr)
        extracted_text += page_text + "\n"
        
    return extracted_text.strip()