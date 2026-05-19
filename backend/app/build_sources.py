from app.source_library import build_source_library


if __name__ == "__main__":
    sources = build_source_library()
    print(f"Built source library with {len(sources)} sources.")
    for source in sources:
        print(f"- {source['filename']} ({source['word_count']} words)")
