import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from app.parser import extract_text
from app.database import load_reference_documents, get_source_names
from app.similarity import plagiarism_score


app = FastAPI(title="AI Plagiarism Checker API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.get("/")
def home():
    return {
        "message": "AI Plagiarism Checker API is running"
    }


@app.get("/sources")
def get_sources():
    sources = get_source_names()

    return {
        "total_sources": len(sources),
        "sources": sources
    }


@app.post("/check")
async def check_plagiarism(
    file: UploadFile = File(None),
    text: str = Form(None)
):
    uploaded_text = ""

    if file:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        uploaded_text = extract_text(file_path)

    elif text:
        uploaded_text = text

    else:
        return {
            "error": "Please upload a file or enter text."
        }

    reference_docs = load_reference_documents()

    if not reference_docs:
        return {
            "error": "No reference documents found."
        }

    result = plagiarism_score(uploaded_text, reference_docs)

    return result