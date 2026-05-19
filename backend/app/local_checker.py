from app.similarity import (
    build_similarity_context,
    calculate_coverage_score,
    find_weighted_sentence_matches,
    get_model_status,
    highlight_user_text,
)
from app.source_library import build_source_library, load_source_library


LOCAL_FULL_TEXT_WEIGHT = 1.0
LOCAL_FULL_TEXT_THRESHOLD = 58
LOCAL_SOURCE_SENTENCE_LIMIT = 300


def _load_or_build_sources() -> list[dict]:
    sources = load_source_library()

    if sources:
        return sources

    return build_source_library()


def check_local_plagiarism(user_text: str):
    sources = _load_or_build_sources()
    similarity_context = build_similarity_context(user_text)

    all_matches = []
    all_sentence_matches = []

    for source in sources:
        sentence_matches = find_weighted_sentence_matches(
            user_text=user_text,
            source_text=source.get("text", ""),
            source_field="full_text",
            evidence_weight=LOCAL_FULL_TEXT_WEIGHT,
            threshold=LOCAL_FULL_TEXT_THRESHOLD,
            context=similarity_context,
            source_sentence_limit=LOCAL_SOURCE_SENTENCE_LIMIT,
        )

        all_sentence_matches.extend(sentence_matches)

        if sentence_matches:
            source_score = round(
                sum(match["weighted_similarity"] for match in sentence_matches)
                / len(sentence_matches),
                2,
            )
            matched_against = "full_text"
        else:
            source_score = 0.0
            matched_against = "no strong match"

        all_matches.append({
            "title": source.get("title", ""),
            "authors": [],
            "journal": "",
            "doi": "",
            "url": "",
            "year": "",
            "type": "local source",
            "filename": source.get("filename", ""),
            "word_count": source.get("word_count", 0),
            "similarity": source_score,
            "matched_against": matched_against,
            "matched_sentences": sentence_matches,
        })

    all_matches = sorted(
        all_matches,
        key=lambda item: item["similarity"],
        reverse=True,
    )

    top_matches = [
        match
        for match in all_matches
        if match["similarity"] > 0
    ][:5]

    overall_similarity = calculate_coverage_score(
        user_text,
        all_sentence_matches,
    )

    highlighted_text = highlight_user_text(
        user_text,
        all_sentence_matches,
    )

    return {
        "overall_similarity": overall_similarity,
        "sources_checked": len(all_matches),
        "sources_with_comparison_text": len(sources),
        "total_sentence_matches": len(all_sentence_matches),
        "model_status": get_model_status(),
        "highlighted_text": highlighted_text,
        "matches": top_matches,
    }
