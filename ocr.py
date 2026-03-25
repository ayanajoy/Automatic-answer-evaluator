import os
import tempfile
import numpy as np
import cv2

# Initialize the PaddleOCR reader (loads models into memory)
# using 'en' for English characters
try:
    from paddleocr import PaddleOCR
    # cls=True helps with detecting text orientation
    ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
except ImportError:
    print("Warning: PaddleOCR not installed. Run: pip install paddlepaddle paddleocr")
    ocr = None


def extract_text_from_image(img_input) -> str:
    """
    Extracts text from a single image using PaddleOCR.
    """
    if ocr is None:
        return "Error: PaddleOCR is not installed"

    if isinstance(img_input, str):
        img = cv2.imread(img_input)
    else:
        img = img_input

    # PaddleOCR inference
    # cls=True turns on the angle classifier
    results = ocr.ocr(img, cls=True)
    
    extracted_text = []
    # results[0] contains the actual bounds and texts if any text was found
    if results and results[0]:
        for line in results[0]:
            # line structure: [[[x1, y1], [x2, y2], [x3, y3], [x4, y4]], ('text', confidence)]
            text = line[1][0]
            extracted_text.append(text)
            
    return "\n".join(extracted_text)

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
        images = convert_from_path(
            pdf_path,
            poppler_path=r"C:\poppler-25.12.0\Library\bin"
        )
    except Exception as e:
        print(f"Error converting PDF to images (ensure Poppler is installed): {e}")
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