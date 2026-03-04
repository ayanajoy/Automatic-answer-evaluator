from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
from .preprocess import preprocess

# Load model once
model = SentenceTransformer('all-MiniLM-L6-v2')


# ==========================================
# Split sentences from student answer
# ==========================================
def split_sentences(text):

    sentences = re.split(r'[.?!]', text)

    cleaned = []

    for s in sentences:
        s = s.strip()
        if len(s) > 3:
            cleaned.append(s)

    return cleaned


# ==========================================
# Detect negation words
# ==========================================
def get_negation_count(text):

    negations = [
        "not",
        "no",
        "never",
        "don't",
        "cannot",
        "neither",
        "nor"
    ]

    count = 0

    for word in negations:
        if re.search(r'\b' + word + r'\b', text.lower()):
            count += 1

    return count


# ==========================================
# Main grading function
# ==========================================
def calculate_marks(model_answer, student_answer, total_marks):

    # --------------------------------------
    # Empty answer check
    # --------------------------------------
    if not student_answer.strip():
        return 0.0, {
            "semantic": 0,
            "keyword": 0,
            "length": 0
        }

    # --------------------------------------
    # Split model answer into concept points
    # --------------------------------------
    model_points = [
        p.strip() for p in model_answer.split('.')
        if len(p.strip()) > 5
    ]

    if not model_points:
        model_points = [model_answer]

    # --------------------------------------
    # Split student answer into sentences
    # --------------------------------------
    student_sentences = split_sentences(student_answer)

    if not student_sentences:
        student_sentences = [student_answer]

    # --------------------------------------
    # Encode student sentences once
    # --------------------------------------
    student_embeddings = model.encode(student_sentences)

    point_scores = []

    # --------------------------------------
    # Compare each model point with best student sentence
    # --------------------------------------
    for point in model_points:

        point_embedding = model.encode([point])

        best_score = 0

        for s_emb in student_embeddings:

            sim = cosine_similarity(point_embedding, [s_emb])[0][0]

            if sim > best_score:
                best_score = sim

        point_scores.append(best_score)

    semantic = float(np.mean(point_scores))

    # --------------------------------------
    # Keyword matching
    # --------------------------------------
    model_words = preprocess(model_answer).split()
    student_clean = preprocess(student_answer)

    unique_keywords = list(set(model_words))

    matched_keywords = 0

    for word in unique_keywords:
        if word in student_clean:
            matched_keywords += 1

    keyword = matched_keywords / len(unique_keywords) if unique_keywords else 0

    # --------------------------------------
    # Negation penalty
    # --------------------------------------
    m_neg = get_negation_count(model_answer)
    s_neg = get_negation_count(student_answer)

    neg_penalty = 1.0

    if (m_neg == 0 and s_neg > 0) or (m_neg > 0 and s_neg == 0):
        neg_penalty = 0.5

    # --------------------------------------
    # Length score
    # --------------------------------------
    model_len = len(model_answer.split())
    student_len = len(student_answer.split())

    length = min(student_len / model_len, 1.0)

    # --------------------------------------
    # Final weighted score
    # --------------------------------------
    final_score = (
        0.70 * semantic +
        0.20 * keyword +
        0.10 * length
    ) * neg_penalty

    marks = float(final_score * total_marks)

    return round(marks, 2), {
        "semantic": round(semantic, 3),
        "keyword": round(keyword, 3),
        "length": round(length, 3),
        "negation_applied": neg_penalty < 1.0
    }