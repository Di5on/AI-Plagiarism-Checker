import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


model = SentenceTransformer("all-MiniLM-L6-v2")


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9.,!? ]", "", text)
    return text.strip()


def split_sentences(text: str):
    sentences = re.split(r"(?<=[.!?]) +", text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]


def calculate_tfidf_similarity(uploaded_text, reference_docs):
    all_texts = [uploaded_text] + [doc["text"] for doc in reference_docs]

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    uploaded_vector = tfidf_matrix[0:1]
    reference_vectors = tfidf_matrix[1:]

    similarities = cosine_similarity(uploaded_vector, reference_vectors)[0]

    results = []

    for index, score in enumerate(similarities):
        results.append({
            "filename": reference_docs[index]["filename"],
            "similarity": round(float(score) * 100, 2)
        })

    return sorted(results, key=lambda x: x["similarity"], reverse=True)


def calculate_embedding_similarity(uploaded_text, reference_docs):
    uploaded_embedding = model.encode([uploaded_text])

    reference_texts = [doc["text"] for doc in reference_docs]
    reference_embeddings = model.encode(reference_texts)

    similarities = cosine_similarity(uploaded_embedding, reference_embeddings)[0]

    results = []

    for index, score in enumerate(similarities):
        results.append({
            "filename": reference_docs[index]["filename"],
            "similarity": round(float(score) * 100, 2)
        })

    return sorted(results, key=lambda x: x["similarity"], reverse=True)


def classify_match(uploaded_sentence, matched_sentence, similarity_score):
    uploaded_words = set(clean_text(uploaded_sentence).split())
    matched_words = set(clean_text(matched_sentence).split())

    if not uploaded_words or not matched_words:
        return "Weak Match"

    word_overlap = len(uploaded_words.intersection(matched_words)) / len(uploaded_words.union(matched_words))

    if similarity_score >= 85 and word_overlap >= 0.45:
        return "Direct Similarity"

    elif similarity_score >= 70 and word_overlap < 0.45:
        return "Possible Paraphrase"

    elif similarity_score >= 60:
        return "Moderate Similarity"

    else:
        return "Weak Match"


def find_matched_sentences(uploaded_text, reference_docs, top_n=8):
    uploaded_sentences = split_sentences(uploaded_text)
    matches = []

    for doc in reference_docs:
        reference_sentences = split_sentences(doc["text"])

        if not uploaded_sentences or not reference_sentences:
            continue

        uploaded_embeddings = model.encode(uploaded_sentences)
        reference_embeddings = model.encode(reference_sentences)

        similarity_matrix = cosine_similarity(uploaded_embeddings, reference_embeddings)

        for i, uploaded_sentence in enumerate(uploaded_sentences):
            best_match_index = np.argmax(similarity_matrix[i])
            best_score = similarity_matrix[i][best_match_index]
            similarity_percentage = round(float(best_score) * 100, 2)

            if similarity_percentage >= 60:
                matched_sentence = reference_sentences[best_match_index]
                match_type = classify_match(
                    uploaded_sentence,
                    matched_sentence,
                    similarity_percentage
                )

                matches.append({
                    "source": doc["filename"],
                    "uploaded_sentence": uploaded_sentence,
                    "matched_sentence": matched_sentence,
                    "similarity": similarity_percentage,
                    "match_type": match_type
                })

    matches = sorted(matches, key=lambda x: x["similarity"], reverse=True)

    return matches[:top_n]


def get_highlighted_text(uploaded_text, matched_sentences):
    highlighted_text = uploaded_text

    for match in matched_sentences:
        sentence = match["uploaded_sentence"]
        match_type = match["match_type"]

        if match_type == "Direct Similarity":
            color = "#ffb3b3"
        elif match_type == "Possible Paraphrase":
            color = "#fff3b0"
        elif match_type == "Moderate Similarity":
            color = "#cce5ff"
        else:
            color = "#eeeeee"

        highlighted_sentence = (
            f"<mark style='background-color:{color}; padding:3px; border-radius:4px;'>"
            f"{sentence}"
            f"</mark>"
        )

        highlighted_text = highlighted_text.replace(sentence, highlighted_sentence)

    return highlighted_text


def plagiarism_score(uploaded_text, reference_docs):
    if not reference_docs:
        return {
            "overall_similarity": 0,
            "top_matches": [],
            "matched_sentences": [],
            "highlighted_text": uploaded_text
        }

    original_uploaded_text = uploaded_text
    cleaned_uploaded_text = clean_text(uploaded_text)

    tfidf_results = calculate_tfidf_similarity(cleaned_uploaded_text, reference_docs)
    embedding_results = calculate_embedding_similarity(cleaned_uploaded_text, reference_docs)

    combined_results = []

    for doc in reference_docs:
        filename = doc["filename"]

        tfidf_score = next(
            item["similarity"] for item in tfidf_results if item["filename"] == filename
        )

        embedding_score = next(
            item["similarity"] for item in embedding_results if item["filename"] == filename
        )

        combined_score = round((tfidf_score * 0.4) + (embedding_score * 0.6), 2)

        combined_results.append({
            "filename": filename,
            "tfidf_similarity": tfidf_score,
            "embedding_similarity": embedding_score,
            "combined_similarity": combined_score
        })

    combined_results = sorted(
        combined_results,
        key=lambda x: x["combined_similarity"],
        reverse=True
    )

    top_matches = combined_results[:5]

    overall_similarity = top_matches[0]["combined_similarity"] if top_matches else 0

    matched_sentences = find_matched_sentences(
        cleaned_uploaded_text,
        reference_docs
    )

    highlighted_text = get_highlighted_text(
        clean_text(original_uploaded_text),
        matched_sentences
    )

    return {
        "overall_similarity": overall_similarity,
        "top_matches": top_matches,
        "matched_sentences": matched_sentences,
        "highlighted_text": highlighted_text
    }