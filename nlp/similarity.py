from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

# Load model once
model = SentenceTransformer('all-MiniLM-L6-v2')


# =====================================
# 1️⃣ Semantic Similarity
# =====================================
def calculate_similarity(model_answer, student_answer):
    embeddings = model.encode([model_answer, student_answer])
    similarity = cosine_similarity(
        [embeddings[0]], 
        [embeddings[1]]
    )[0][0]
    return float(similarity)


# =====================================
# 2️⃣ Keyword Extraction
# =====================================
def extract_keywords(text):
    # Simple keyword extraction (can upgrade later)
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    
    # Remove common stop words manually (basic version)
    stopwords = {
        "this", "that", "with", "from", "into", 
        "using", "there", "their", "have", "been",
        "will", "shall", "about", "which"
    }
    
    keywords = [w for w in words if w not in stopwords]
    
    # Unique keywords only
    return list(set(keywords))


# =====================================
# 3️⃣ Keyword Matching Score
# =====================================
def keyword_score(model_answer, student_answer):
    model_keywords = extract_keywords(model_answer)
    student_text = student_answer.lower()
    
    if not model_keywords:
        return 0

    matched = 0
    for word in model_keywords:
        if word in student_text:
            matched += 1

    return matched / len(model_keywords)


# =====================================
# 4️⃣ Length Score
# =====================================
def length_score(model_answer, student_answer):
    model_len = len(model_answer.split())
    student_len = len(student_answer.split())

    if model_len == 0:
        return 0

    ratio = student_len / model_len

    # Cap at 1 (no extra benefit for very long answer)
    return min(ratio, 1.0)


# =====================================
# 5️⃣ Final Hybrid Mark Calculation
# =====================================
def calculate_marks(model_answer, student_answer, total_marks):

    semantic = calculate_similarity(model_answer, student_answer)
    keyword = keyword_score(model_answer, student_answer)
    length = length_score(model_answer, student_answer)

    final_score = (
        0.6 * semantic +
        0.25 * keyword +
        0.15 * length
    )

    marks = final_score * total_marks

    return round(marks, 2), {
        "semantic": round(semantic, 3),
        "keyword": round(keyword, 3),
        "length": round(length, 3)
    }