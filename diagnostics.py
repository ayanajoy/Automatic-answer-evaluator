import sys
import os

# Set base path
sys.path.append(os.getcwd())

print("--- EduAI Diagnostic Tool ---")

# 1. Check ML Scoring
try:
    from nlp.similarity import calculate_marks
    print("[✓] NLP Module: Loaded successfully.")
    
    model_ans = "The capital of France is Paris. It is known for the Eiffel Tower."
    student_ans = "Paris is the capital of France."
    marks, breakdown = calculate_marks(model_ans, student_ans, 10)
    
    print(f"[✓] ML Scoring: Working! (Scored {marks}/10)")
    print(f"    Details: {breakdown}")
except Exception as e:
    print(f"[×] NLP Error: {e}")

# 2. Check OCR Engine
try:
    import easyocr
    reader = easyocr.Reader(['en'])
    print("[✓] EasyOCR: Engine initialized successfully.")
except Exception as e:
    print(f"[×] EasyOCR Error: {e}")

# 3. Check Poppler (for PDF processing)
try:
    from pdf2image import convert_from_path
    import tempfile
    
    # Check if poppler is in PATH by trying to run a dummy conversion
    # (This will fail if poppler is missing, but we catch it)
    print("Checking Poppler dependency...")
    # Attempting to check if 'pdftoppm' or similar exists (low-level check)
    import subprocess
    try:
        subprocess.run(['pdftoppm', '-h'], capture_output=True)
        print("[✓] Poppler: Found in system PATH.")
    except FileNotFoundError:
        print("[×] Poppler Error: 'pdftoppm' not found. Please install Poppler and add its /bin folder to your PATH.")

except Exception as e:
    print(f"[i] Note: pdf2image is installed, but system verification skipped ({e})")

print("\n--- Diagnostic Complete ---")