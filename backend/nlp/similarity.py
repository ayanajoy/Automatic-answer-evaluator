import nltk
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load model only once
model = SentenceTransformer('all-MiniLM-L6-v2')


def calculate_similarity(model_answer, student_answer):

    # Split answers into sentences
    model_sentences = nltk.sent_tokenize(model_answer)
    student_sentences = nltk.sent_tokenize(student_answer)

    # Edge case: if empty
    if not model_sentences or not student_sentences:
        return 0.0

    # Encode sentences
    model_embeddings = model.encode(model_sentences)
    student_embeddings = model.encode(student_sentences)

    # Compute similarity matrix
    similarity_matrix = cosine_similarity(model_embeddings, student_embeddings)

    # Take best match for each model sentence
    max_similarities = similarity_matrix.max(axis=1)

    # Average similarity
    final_similarity = max_similarities.mean()

    return float(final_similarity)


def calculate_marks(similarity, total_marks):
    return round(similarity * total_marks, 2)