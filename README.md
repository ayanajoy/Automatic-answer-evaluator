# EduAI | Automatic Answer Sheet Evaluator 🎓

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/framework-FastAPI-green.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

**EduAI** is a next-generation institutional assessment platform designed to automate the evaluation of descriptive answer sheets. By leveraging **Optical Character Recognition (OCR)** and **Natural Language Processing (NLP)**, it transforms traditional grading into a fast, consistent, and intelligent process.

---

## 🌟 Key Features

- 🎯 **Dual-Portal System**: Separate interfaces for **Faculty** (exam management & analytics) and **Students** (answer submission).
- ✍️ **Hybrid Digitization**: Supports both typed responses and **handwritten PDF/image uploads** using PaddleOCR.
- 🧠 **Smart Evaluation**: Uses **Semantic Similarity (SBERT)** to evaluate answers based on meaning, not just keywords.
- 📊 **Automated Insights**: Generates instant marks and performance analytics.
- ⚖️ **Logical Evaluation**: Detects contradictions and performs fuzzy keyword matching.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite
- **OCR Engine**: PaddleOCR, pdfplumber
- **NLP Models**: Sentence-Transformers (`all-MiniLM-L6-v2`)
- **Image Processing**: OpenCV
- **Frontend**: HTML5, CSS3, JavaScript

---

## 🏗️ System Workflow

```text
Student Input → OCR → Preprocessing → NLP (SBERT) → Evaluation → Database → Result
```

---

## 🚀 Getting Started

### 🔧 Prerequisites
- Python 3.9+
- Poppler (required for PDF processing)

---

### 📥 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ayanajoy/Automatic-answer-evaluator.git
   cd Automatic-answer-evaluator
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   uvicorn main:app --reload
   ```

5. **Open in browser**:
   `http://127.0.0.1:8000`

---

## 📊 Scoring Mechanism

| Component | Weight | Description |
| :--- | :--- | :--- |
| **Semantic Similarity** | 65% | Meaning-based evaluation using SBERT |
| **Keyword Matching** | 25% | Important term matching with fuzzy logic |
| **Answer Completeness** | 10% | Coverage and length of answer |

> [!NOTE]
> The system also applies penalties for contradictions (negation) and excessive repetition.

---

## 🔮 Future Scope
- Integration with Large Language Models (LLMs).
- Multilingual support.
- Improved handwriting recognition.
- Detailed feedback generation.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <b>EduAI © 2026 | Academic Project</b>
</div>
