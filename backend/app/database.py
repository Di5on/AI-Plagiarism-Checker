import os
from app.parser import extract_text


REFERENCE_FOLDER = "reference_docs"


def load_reference_documents():
    documents = []

    if not os.path.exists(REFERENCE_FOLDER):
        os.makedirs(REFERENCE_FOLDER)

    for filename in os.listdir(REFERENCE_FOLDER):
        file_path = os.path.join(REFERENCE_FOLDER, filename)

        if os.path.isfile(file_path):
            try:
                text = extract_text(file_path)

                documents.append({
                    "filename": filename,
                    "text": text
                })

            except Exception as e:
                print(f"Error loading {filename}: {e}")

    return documents


def get_source_names():
    documents = load_reference_documents()
    return [doc["filename"] for doc in documents]