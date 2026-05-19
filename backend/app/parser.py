import fitz
import docx


async def extract_text_from_file(file):
    filename = file.filename.lower()
    content = await file.read()

    if filename.endswith(".txt"):
        return content.decode("utf-8", errors="ignore")

    elif filename.endswith(".pdf"):
        text = ""
        pdf = fitz.open(stream=content, filetype="pdf")

        for page in pdf:
            text += page.get_text()

        return text

    elif filename.endswith(".docx"):
        temp_path = "temp_uploaded.docx"

        with open(temp_path, "wb") as f:
            f.write(content)

        document = docx.Document(temp_path)

        text = ""
        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"

        return text

    else:
        return ""