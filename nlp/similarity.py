from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import nltk
from .preprocess import preprocess

import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load model once with error handling for network issues
MODEL_NAME = 'all-MiniLM-L6-v2'

try:
    logger.info(f"Loading SentenceTransformer model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
except Exception as e:
    logger.warning(f"Failed to load model from Hugging Face Hub: {e}")
    logger.info("Attempting to load in offline mode...")
    try:
        # Set offline mode if initial load fails (likely DNS/Network issue)
        os.environ["HF_HUB_OFFLINE"] = "1"
        model = SentenceTransformer(MODEL_NAME)
        logger.info("Successfully loaded model from local cache.")
    except Exception as e_offline:
        logger.error(f"Critical Error: Could not load model even from cache. {e_offline}")
        logger.error("Please ensure you have an active internet connection for the first-time setup or the model is manually downloaded.")
        # Fallback or raise a more descriptive error
        raise RuntimeError(
            "Model loading failed. If this is the first run, you need internet to download the model. "
            "Check your connection or DNS settings. Once downloaded, the app can run offline."
        ) from e_offline

# Ensure tokenizer available
nltk.download('punkt', quiet=True)

# ==========================================
# Split sentences properly using NLTK
# ==========================================
def split_sentences(text):
    sentences = nltk.sent_tokenize(text)
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
    negations = ["not", "no", "never", "don't", "cannot", "neither", "nor", "none"]
    count = 0
    for word in negations:
        if re.search(r'\b' + word + r'\b', text.lower()):
            count += 1
    return count

# ==========================================
# Main grading function (Advanced Local NLP)
# ==========================================
def calculate_marks(model_answer, student_answer, total_marks):
    
    # --------------------------------------
    # 1. Edge Case: Empty Answer
    # --------------------------------------
    if not student_answer.strip():
        return 0.0, {
            "semantic": 0, "keyword": 0, "length": 0, 
            "concept_coverage": "0/0", "is_llm": False, 
            "explanation": "No valid answer provided or OCR completely failed."
        }

    # --------------------------------------
    # 1.5 OCR Contextual Spell-Check (Repairs garbled text)
    # --------------------------------------
    # OCR creates nonsense words. We use the teacher's model answer as a dictionary
    # to "snap" garbled student words back to the correct spelling.
    import difflib
    
    # Get teacher's vocabulary (only words 4+ chars to avoid snapping 'is' to 'it')
    model_vocab = [w for w in preprocess(model_answer).split() if len(w) > 3]
    
    corrected_student = []
    for word in student_answer.split():
        clean_w = preprocess(word)
        if len(clean_w) > 3 and clean_w not in model_vocab:
            # Snap to teacher's vocabulary with a forgiving OCR cutoff (55% similarity)
            # This fixes 'leoYning' -> 'learning' and 'pgepIocessinq' -> 'preprocessing'
            matches = difflib.get_close_matches(clean_w, model_vocab, n=1, cutoff=0.55)
            if matches:
                 corrected_student.append(matches[0])
                 continue
        corrected_student.append(word)
        
    # Reassemble the student answer with fixed OCR typos
    student_answer = " ".join(corrected_student)
        
    # --------------------------------------
    # 2. Extract Key Concepts from Model
    # --------------------------------------
    model_points = [p.strip() for p in model_answer.split('.') if len(p.strip()) > 5]
    if not model_points:
        model_points = [model_answer]

    student_sentences = split_sentences(student_answer)
    if not student_sentences:
        student_sentences = [student_answer]

    # Encode texts
    student_embeddings = model.encode(student_sentences)
    model_embeddings = model.encode(model_points)
    
    # --------------------------------------
    # 3. Semantic Sentence Matching (Concept Coverage)
    # --------------------------------------
    point_scores = []
    for m_emb in model_embeddings:
        best_score = 0
        for s_emb in student_embeddings:
            sim = cosine_similarity([m_emb], [s_emb])[0][0]
            if sim > best_score:
                best_score = sim
        point_scores.append(best_score)
        
    # How many core concepts were explicitly addressed?
    coverage_threshold = 0.55 # Lowered threshold to account for bad handwriting/OCR
    covered_points = sum(1 for score in point_scores if score >= coverage_threshold)
    
    # Base Semantic Score
    semantic_score = covered_points / max(len(point_scores), 1)
    
    # If the student wrote a good chunk that generally matches the whole answer, boost them
    full_student_emb = model.encode([student_answer])
    full_model_emb = model.encode([model_answer])
    overall_sim = cosine_similarity(full_model_emb, full_student_emb)[0][0]
    
    # Pick the best semantic representation
    final_semantic = max(semantic_score, overall_sim)

    # --------------------------------------
    # 4. Fuzzy Keyword Matching (OCR Resilient)
    # --------------------------------------
    import difflib
    
    model_words = preprocess(model_answer).split()
    student_clean = preprocess(student_answer)
    student_words = student_clean.split()
    unique_keywords = list(set(model_words))
    
    matched_keywords = 0
    for expected_word in unique_keywords:
        # 1. Try exact match first
        if f" {expected_word} " in f" {student_clean} ":
            matched_keywords += 1
        else:
            # 2. Try fuzzy match for OCR typos (e.g. 'learning' -> 'leoYning')
            # cutoff=0.72 allows 1-2 character OCR mistakes per word
            matches = difflib.get_close_matches(expected_word, student_words, n=1, cutoff=0.72)
            if matches:
                matched_keywords += 1

    keyword_score = matched_keywords / len(unique_keywords) if unique_keywords else 1.0

    # --------------------------------------
    # 5. Logical Penalties (Negations)
    # --------------------------------------
    m_neg = get_negation_count(model_answer)
    s_neg = get_negation_count(student_answer)
    
    # If model says "is" but student says "is not" -> massive penalty
    neg_penalty = 1.0
    if (m_neg == 0 and s_neg > 0) or (m_neg > 0 and s_neg == 0):
        neg_penalty = 0.5

    # --------------------------------------
    # 6. Length and Repetition Checks
    # --------------------------------------
    model_len = len(model_answer.split())
    student_len = len(student_answer.split())
    
    length_score = min(student_len / max(model_len, 1), 1.0)
    if student_len < model_len * 0.3:
        length_score *= 0.5 # Too short
        
    words = student_answer.split()
    unique_ratio = len(set(words)) / max(len(words), 1)
    # If they just wrote the same word 50 times to trick the length score:
    rep_penalty = 0.7 if unique_ratio < 0.4 else 1.0

    # --------------------------------------
    # 7. Final Weighted Calculation
    # --------------------------------------
    # Weighting: 65% Semantic meaning, 25% Keyword exact matches, 10% Length
    raw_final = (0.65 * final_semantic + 0.25 * keyword_score + 0.10 * length_score)
    final_score = raw_final * neg_penalty * rep_penalty
    
    # Round marks
    marks_awarded = round(float(final_score * total_marks), 2)
    # Don't let bad OCR drag a theoretically perfect answer down to 0
    if marks_awarded < 0: marks_awarded = 0
    if marks_awarded > total_marks: marks_awarded = total_marks

    return marks_awarded, {
        "semantic": round(final_semantic, 3),
        "keyword": round(keyword_score, 3),
        "length": round(length_score, 3),
        "concept_coverage": f"{covered_points}/{len(point_scores)}",
        "negation_applied": neg_penalty < 1.0,
        "is_llm": False
    }

def generate_explanation(breakdown):
    if breakdown.get("is_llm", False) and "explanation" in breakdown:
        return breakdown["explanation"]

    explanation = []
    
    if breakdown.get("semantic", 0) > 0.75:
        explanation.append("Strong conceptual understanding shown.")
    elif breakdown.get("semantic", 0) > 0.5:
        explanation.append("Moderate understanding, but missed key nuances.")
    else:
        explanation.append("Answer lacks core concepts.")
        
    if breakdown.get("keyword", 0) > 0.7:
        explanation.append("Excellent use of specific terminology.")
    elif breakdown.get("keyword", 0) < 0.3:
        explanation.append("Missing crucial vocabulary keywords.")
        
    if breakdown.get("negation_applied", False):
        explanation.append("Logical contradiction detected (e.g. said 'not' when shouldn't).")

    return " ".join(explanation)