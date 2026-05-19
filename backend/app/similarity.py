import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer


MODEL_NAME = "all-MiniLM-L6-v2"
model = None
model_load_error = None


def get_model():
    global model, model_load_error

    if model is not None or model_load_error is not None:
        return model

    try:
        model = SentenceTransformer(MODEL_NAME, local_files_only=True)
    except Exception as error:
        model_load_error = str(error)
        try:
            model = SentenceTransformer(MODEL_NAME)
            model_load_error = None
        except Exception as download_error:
            model_load_error = str(download_error)
            model = None

    return model


def get_model_status():
    embedding_model = get_model()

    return {
        "model_name": MODEL_NAME,
        "available": embedding_model is not None,
        "error": model_load_error,
    }


def semantic_similarity(text1: str, text2: str) -> float:
    if not text1 or not text2:
        return 0.0

    embedding_model = get_model()

    if embedding_model is None:
        return 0.0

    embeddings = embedding_model.encode([text1, text2])

    score = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]]
    )[0][0]

    return round(float(score) * 100, 2)


def tfidf_similarity(text1: str, text2: str) -> float:
    if not text1 or not text2:
        return 0.0

    vectorizer = TfidfVectorizer(stop_words="english")

    try:
        vectors = vectorizer.fit_transform([text1, text2])
        score = cosine_similarity(vectors[0], vectors[1])[0][0]
        return round(float(score) * 100, 2)

    except ValueError:
        return 0.0


def combined_similarity(text1: str, text2: str) -> float:
    semantic_score = semantic_similarity(text1, text2)
    tfidf_score = tfidf_similarity(text1, text2)

    if get_model() is None:
        return tfidf_score

    final_score = (semantic_score * 0.65) + (tfidf_score * 0.35)

    return round(final_score, 2)


def split_sentences(text: str, max_sentences: int | None = None):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    cleaned_sentences = [s.strip() for s in sentences if len(s.strip()) > 30]

    if max_sentences is not None:
        return cleaned_sentences[:max_sentences]

    return cleaned_sentences


@dataclass
class SimilarityContext:
    user_sentences: list[str]
    user_embeddings: object


def build_similarity_context(user_text: str) -> SimilarityContext:
    user_sentences = split_sentences(user_text)
    embedding_model = get_model()
    user_embeddings = (
        embedding_model.encode(user_sentences)
        if embedding_model is not None and user_sentences
        else []
    )

    return SimilarityContext(
        user_sentences=user_sentences,
        user_embeddings=user_embeddings,
    )


def tokenize_words(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z'-]{2,}", text.lower())
    stop_words = {
        "the", "and", "for", "that", "this", "with", "from", "have",
        "has", "had", "are", "was", "were", "not", "but", "you",
        "your", "their", "there", "they", "into", "about", "between",
        "within", "using", "used", "use", "can", "could", "should",
    }
    return {word for word in words if word not in stop_words}


def normalize_for_exact_match(text: str) -> str:
    text = text.lower()
    text = re.sub(r"-\s+", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def exact_normalized_match(text1: str, text2: str) -> bool:
    normalized_text1 = normalize_for_exact_match(text1)
    normalized_text2 = normalize_for_exact_match(text2)

    return bool(normalized_text1 and normalized_text1 == normalized_text2)


def fuzzy_similarity(text1: str, text2: str) -> float:
    normalized_text1 = normalize_for_exact_match(text1)
    normalized_text2 = normalize_for_exact_match(text2)

    if not normalized_text1 or not normalized_text2:
        return 0.0

    return round(
        SequenceMatcher(None, normalized_text1, normalized_text2).ratio() * 100,
        2,
    )


def lexical_overlap(text1: str, text2: str) -> float:
    words1 = tokenize_words(text1)
    words2 = tokenize_words(text2)

    if not words1 or not words2:
        return 0.0

    return len(words1 & words2) / len(words1)


def classify_match(
    score: float,
    fuzzy_score: float,
    lexical_overlap_score: float,
    is_exact_match: bool,
) -> dict:
    if is_exact_match or fuzzy_score >= 97:
        return {
            "match_type": "Direct Match",
            "highlight_color": "#ff8a80",
            "border_color": "#d32f2f",
        }

    if fuzzy_score >= 88 or (score >= 88 and lexical_overlap_score >= 0.72):
        return {
            "match_type": "Near-Exact / Lightly Edited",
            "highlight_color": "#ffcc80",
            "border_color": "#f57c00",
        }

    if score >= 70 and lexical_overlap_score < 0.55:
        return {
            "match_type": "Paraphrased / Semantic Match",
            "highlight_color": "#fff176",
            "border_color": "#fbc02d",
        }

    return {
        "match_type": "Moderate Similarity",
        "highlight_color": "#bbdefb",
        "border_color": "#1976d2",
    }


def tfidf_pair_scores(user_sentences: list[str], source_sentence: str) -> list[float]:
    if not user_sentences or not source_sentence:
        return [0.0 for _ in user_sentences]

    vectorizer = TfidfVectorizer(stop_words="english")

    try:
        vectors = vectorizer.fit_transform(user_sentences + [source_sentence])
    except ValueError:
        return [0.0 for _ in user_sentences]

    scores = cosine_similarity(vectors[:-1], vectors[-1])
    return [float(score[0]) * 100 for score in scores]


def find_weighted_sentence_matches(
    user_text: str,
    source_text: str,
    source_field: str,
    evidence_weight: float,
    threshold: float = 58,
    context: SimilarityContext | None = None,
    source_sentence_limit: int | None = None,
):
    context = context or build_similarity_context(user_text)
    user_sentences = context.user_sentences
    if source_sentence_limit is None and source_field == "full_text":
        source_sentence_limit = 80
    source_sentences = split_sentences(
        source_text,
        max_sentences=source_sentence_limit,
    )

    if source_field == "title" and source_text.strip():
        source_sentences = [source_text.strip()]

    if not user_sentences or not source_sentences:
        return []

    embedding_model = get_model()

    if embedding_model is not None and len(context.user_embeddings) > 0:
        source_embeddings = embedding_model.encode(source_sentences)
        semantic_matrix = cosine_similarity(
            context.user_embeddings,
            source_embeddings,
        )
    else:
        semantic_matrix = None

    tfidf_by_source = [
        tfidf_pair_scores(user_sentences, source_sentence)
        for source_sentence in source_sentences
    ]

    matches = []

    for user_index, user_sentence in enumerate(user_sentences):
        best_match = None
        best_score = 0.0
        best_overlap = 0.0
        best_fuzzy_score = 0.0
        best_exact_match = False

        for source_index, source_sentence in enumerate(source_sentences):
            overlap = lexical_overlap(user_sentence, source_sentence)

            if source_field == "title" and overlap < 0.35:
                continue

            tfidf_score = tfidf_by_source[source_index][user_index]
            fuzzy_score = fuzzy_similarity(user_sentence, source_sentence)
            is_exact_match = exact_normalized_match(user_sentence, source_sentence)

            if is_exact_match:
                score = 100.0
            elif fuzzy_score >= 88:
                score = max(tfidf_score, fuzzy_score)
            elif semantic_matrix is None:
                score = tfidf_score
            else:
                semantic_score = float(semantic_matrix[user_index][source_index]) * 100
                score = (semantic_score * 0.65) + (tfidf_score * 0.35)

            if score > best_score:
                best_score = score
                best_match = source_sentence
                best_overlap = overlap
                best_fuzzy_score = fuzzy_score
                best_exact_match = is_exact_match

        weighted_score = round(best_score * evidence_weight, 2)

        if best_match and best_score >= threshold and weighted_score >= 20:
            classification = classify_match(
                score=best_score,
                fuzzy_score=best_fuzzy_score,
                lexical_overlap_score=best_overlap,
                is_exact_match=best_exact_match,
            )

            matches.append({
                "user_sentence": user_sentence,
                "source_sentence": best_match,
                "source_field": source_field,
                "similarity": round(best_score, 2),
                "weighted_similarity": weighted_score,
                "evidence_weight": evidence_weight,
                "lexical_overlap": round(best_overlap * 100, 2),
                "fuzzy_similarity": best_fuzzy_score,
                "exact_match": best_exact_match,
                **classification,
            })

    return matches


def find_matched_sentences(user_text: str, source_text: str, threshold: float = 55):
    return find_weighted_sentence_matches(
        user_text=user_text,
        source_text=source_text,
        source_field="abstract",
        evidence_weight=0.85,
        threshold=threshold,
    )


def calculate_coverage_score(user_text: str, matched_sentences: list):
    best_by_sentence = {}

    for match in matched_sentences:
        sentence = match.get("user_sentence", "")
        score = match.get("weighted_similarity", match.get("similarity", 0))

        if not sentence:
            continue

        previous_score = best_by_sentence.get(sentence, 0)

        if score > previous_score:
            best_by_sentence[sentence] = score

    total_words = len(user_text.split())

    if total_words == 0:
        return 0.0

    matched_word_score = 0.0

    for sentence, score in best_by_sentence.items():
        matched_word_score += len(sentence.split()) * (score / 100)

    return round(min((matched_word_score / total_words) * 100, 100), 2)


def highlight_user_text(user_text: str, matched_sentences: list):
    highlighted_text = user_text

    sorted_matches = sorted(
        matched_sentences,
        key=lambda x: len(x.get("user_sentence", "")),
        reverse=True
    )

    for match in sorted_matches:
        sentence = match.get("user_sentence", "")

        if not sentence:
            continue

        escaped_sentence = re.escape(sentence)
        color = match.get("highlight_color", "#fff176")
        match_type = match.get("match_type", "Similarity Match")

        highlighted_text = re.sub(
            escaped_sentence,
            (
                f"<mark title=\"{match_type}\" "
                f"style=\"background-color: {color}; "
                "padding: 3px 5px; border-radius: 4px; "
                "font-weight: bold;\">"
                f"{sentence}</mark>"
            ),
            highlighted_text,
            count=1
        )

    return highlighted_text
