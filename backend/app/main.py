from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from app.parser import extract_text_from_file
from app.local_checker import check_local_plagiarism
from app.source_library import build_source_library, load_source_library


app = FastAPI(
    title="AI Plagiarism Checker",
    description="Local source library plagiarism checker using weighted NLP similarity.",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "AI Plagiarism Checker API is running."
    }


@app.get("/local-sources")
def local_sources():
    sources = load_source_library()

    return {
        "total_sources": len(sources),
        "sources": [
            {
                "filename": source.get("filename", ""),
                "title": source.get("title", ""),
                "word_count": source.get("word_count", 0),
            }
            for source in sources
        ],
    }


@app.post("/build-local-sources")
def build_local_sources():
    sources = build_source_library()

    return {
        "total_sources": len(sources),
        "sources": [
            {
                "filename": source.get("filename", ""),
                "title": source.get("title", ""),
                "word_count": source.get("word_count", 0),
            }
            for source in sources
        ],
    }


@app.post("/check-local")
async def check_local(
    text: str = Form(None),
    file: UploadFile = File(None)
):
    if file:
        user_text = await extract_text_from_file(file)

    elif text:
        user_text = text

    else:
        return {
            "error": "Please upload a file or enter text."
        }

    if not user_text.strip():
        return {
            "error": "No readable text found."
        }

    result = check_local_plagiarism(user_text)

    return result

