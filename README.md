# AI Plagiarism Checker

A local source-library plagiarism checker that analyzes uploaded documents or pasted text, compares them against stored source documents, and highlights matched passages with weighted similarity scoring.

---

## Project Overview

This prototype demonstrates plagiarism detection over a controlled local database of source documents. It does not claim internet-wide coverage. Instead, it proves the core detection workflow: ingest sources, extract text, compare submissions, classify match types, calculate similarity coverage, and highlight matched text.

---

## Features

* Upload `.txt`, `.pdf`, and `.docx` submissions
* Paste text directly for checking
* Compare against local source documents from `backend/source_library/`
* Build `backend/data/sources.json` from stored source files
* Exact normalized matching for direct copied text
* Fuzzy matching for lightly edited or PDF-extraction differences
* TF-IDF and Sentence Transformer semantic matching
* Sentence-level match reporting
* Color-coded highlighting:
  * Red: direct match
  * Orange: near-exact or lightly edited
  * Yellow: paraphrased or semantic match
  * Blue: moderate similarity
* FastAPI backend with REST API
* Streamlit frontend

---

## How It Works

```text
Local Source Files (.pdf / .txt / .docx)
        |
Extract Text
        |
Save backend/data/sources.json
        |
User Submission (File / Text)
        |
Sentence Splitting
        |
Exact + Fuzzy + TF-IDF + Semantic Matching
        |
Coverage-Based Similarity Score
        |
Results + Colored Highlights
```

---

## Project Structure

```text
AI-Plagiarism-Checker/
|
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- parser.py
|   |   |-- similarity.py
|   |   |-- source_library.py
|   |   |-- local_checker.py
|   |   |-- build_sources.py
|   |
|   |-- source_library/
|   |-- data/
|   |   |-- sources.json
|   |-- requirements.txt
|
|-- frontend/
|   |-- app.py
|   |-- requirements.txt
|
|-- README.md
|-- .gitignore
```

---

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
```

Activate on Windows:

```bash
venv\Scripts\activate
```

If PowerShell blocks activation, use the venv Python directly:

```powershell
.\venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
```

### 2. Install Dependencies

```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### 3. Add Source Documents

Put trusted source files here:

```text
backend/source_library/
```

Supported formats:

```text
.pdf
.txt
.docx
```

### 4. Build Local Source Database

```bash
cd backend
python -m app.build_sources
```

This creates or updates:

```text
backend/data/sources.json
```

---

## Running The Application

### Start Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Or without activating the venv:

```powershell
cd backend
..\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

### Start Frontend

```bash
cd frontend
streamlit run app.py
```

Or without activating the venv:

```powershell
.\venv\Scripts\python.exe -m streamlit run .\frontend\app.py
```

---

## API Endpoints

### GET /

Returns a basic health message.

### GET /local-sources

Returns the sources currently loaded from `backend/data/sources.json`.

### POST /build-local-sources

Rebuilds `backend/data/sources.json` from files in `backend/source_library/`.

### POST /check-local

Accepts:

* File upload
* Text input

Returns:

```json
{
  "overall_similarity": 98.17,
  "sources_checked": 5,
  "sources_with_comparison_text": 5,
  "total_sentence_matches": 3,
  "matches": [],
  "highlighted_text": "<html>"
}
```

---

## Scoring

The score is based on how much of the submitted text is covered by strong matches.

Matching layers:

* **Exact normalized match**: catches direct copied text even if punctuation, casing, or spacing changes.
* **Fuzzy match**: catches lightly edited text and PDF extraction differences.
* **TF-IDF match**: catches strong keyword and phrase overlap.
* **Semantic match**: catches paraphrased text when the Sentence Transformer model is available.

The app tries to load `all-MiniLM-L6-v2`. If the model is unavailable, it still works with exact, fuzzy, and TF-IDF matching.

---

## Technologies Used

* Python
* FastAPI
* Streamlit
* Scikit-learn
* Sentence Transformers
* PyMuPDF
* python-docx

---

## Limitations

* Checks only sources stored in the local source library.
* Accuracy depends on source quality and PDF text extraction quality.
* Basic sentence segmentation.
* Semantic paraphrase detection depends on the Hugging Face model being available locally or downloadable.

---

## Future Improvements

* Add source upload/import from the frontend.
* Store sources in SQLite instead of JSON.
* Add FAISS or Chroma vector indexing for larger libraries.
* Export similarity reports as PDF.
* Add quote/reference exclusion controls.
