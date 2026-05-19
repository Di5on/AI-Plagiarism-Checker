import json
import re
from pathlib import Path

import docx
import fitz


BACKEND_DIR = Path(__file__).resolve().parents[1]
SOURCE_LIBRARY_DIR = BACKEND_DIR / "source_library"
DATA_DIR = BACKEND_DIR / "data"
SOURCES_JSON = DATA_DIR / "sources.json"


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _extract_pdf_text(path: Path) -> str:
    text_parts = []

    with fitz.open(path) as pdf:
        for page in pdf:
            text_parts.append(page.get_text())

    return _clean_text(" ".join(text_parts))


def _extract_docx_text(path: Path) -> str:
    document = docx.Document(path)
    return _clean_text("\n".join(paragraph.text for paragraph in document.paragraphs))


def _extract_txt_text(path: Path) -> str:
    return _clean_text(path.read_text(encoding="utf-8", errors="ignore"))


def extract_source_text(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf_text(path)

    if suffix == ".docx":
        return _extract_docx_text(path)

    if suffix == ".txt":
        return _extract_txt_text(path)

    return ""


def build_source_library() -> list[dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_LIBRARY_DIR.mkdir(parents=True, exist_ok=True)

    sources = []
    supported_files = sorted(
        path
        for path in SOURCE_LIBRARY_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in {".pdf", ".docx", ".txt"}
    )

    for index, path in enumerate(supported_files, start=1):
        text = extract_source_text(path)

        if not text:
            continue

        sources.append({
            "id": path.stem,
            "filename": path.name,
            "title": path.stem.replace("_", " ").replace("-", " "),
            "path": str(path.relative_to(BACKEND_DIR)),
            "text": text,
            "word_count": len(text.split()),
            "source_number": index,
        })

    SOURCES_JSON.write_text(
        json.dumps(sources, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return sources


def load_source_library() -> list[dict]:
    if not SOURCES_JSON.exists():
        return []

    return json.loads(SOURCES_JSON.read_text(encoding="utf-8"))
