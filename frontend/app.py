import streamlit as st
import requests
import html
import streamlit.components.v1 as components


API_URL = "http://127.0.0.1:8000"


def safe_html(text):
    if text is None:
        return ""
    return html.escape(str(text)).replace("\n", "<br>")


def render_html_box(content, height=300):
    components.html(
        content,
        height=height,
        scrolling=True
    )


st.set_page_config(
    page_title="AI Plagiarism Checker",
    page_icon="📄",
    layout="wide"
)


st.title("AI Plagiarism Checker")

st.write(
    "Check uploaded documents or pasted text against the local source library."
)


st.sidebar.title("About")
st.sidebar.write(
    "This app uses FastAPI, Streamlit, local sources, TF-IDF, fuzzy matching, and Sentence Transformers."
)


input_method = st.radio(
    "Choose input method",
    ["Paste Text", "Upload File"]
)


user_text = ""
uploaded_file = None


if input_method == "Paste Text":
    user_text = st.text_area(
        "Paste your text here",
        height=300
    )
else:
    uploaded_file = st.file_uploader(
        "Upload a file",
        type=["txt", "pdf", "docx"]
    )


if st.button("Check Plagiarism"):

    if input_method == "Paste Text" and not user_text.strip():
        st.error("Please enter some text first.")

    elif input_method == "Upload File" and uploaded_file is None:
        st.error("Please upload a file first.")

    else:
        endpoint = "/check-local"
        spinner_text = "Checking plagiarism using the local source library..."

        with st.spinner(spinner_text):

            try:
                if uploaded_file is not None:
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file,
                            uploaded_file.type
                        )
                    }

                    response = requests.post(
                        f"{API_URL}{endpoint}",
                        files=files
                    )

                else:
                    data = {
                        "text": user_text
                    }

                    response = requests.post(
                        f"{API_URL}{endpoint}",
                        data=data
                    )

                result = response.json()

                if "error" in result:
                    st.error(result["error"])

                else:
                    st.subheader("Overall Similarity")

                    st.metric(
                        label="Similarity Score",
                        value=f"{result.get('overall_similarity', 0)}%"
                    )

                    st.write(
                        f"Sources checked: {result.get('sources_checked', 0)}"
                    )
                    st.write(
                        "Sources with text:",
                        result.get("sources_with_comparison_text", 0)
                    )
                    st.write(
                        "Sentence matches:",
                        result.get("total_sentence_matches", 0)
                    )
                    if result.get("pdf_check_enabled"):
                        st.write(
                            "PDFs checked:",
                            result.get("pdfs_checked", 0)
                        )

                    model_status = result.get("model_status", {})

                    if model_status:
                        if model_status.get("available"):
                            st.success(
                                f"Semantic model active: {model_status.get('model_name')}"
                            )
                        else:
                            st.warning(
                                "Semantic model unavailable. "
                                "Using exact, fuzzy, and TF-IDF matching only."
                            )

                    st.subheader("Highlighted Submitted Text")

                    st.markdown(
                        """
                        <div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:10px;">
                            <span style="background:#ff8a80; padding:5px 8px; border-radius:4px;">Direct Match</span>
                            <span style="background:#ffcc80; padding:5px 8px; border-radius:4px;">Near-Exact / Lightly Edited</span>
                            <span style="background:#fff176; padding:5px 8px; border-radius:4px;">Paraphrased / Semantic</span>
                            <span style="background:#bbdefb; padding:5px 8px; border-radius:4px;">Moderate Similarity</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    highlighted_text = result.get("highlighted_text", "")

                    if highlighted_text:
                        highlighted_box = f"""
                        <html>
                        <head>
                            <style>
                                body {{
                                    font-family: Arial, sans-serif;
                                    background-color: #f8f9fa;
                                    color: #111;
                                    line-height: 1.8;
                                    padding: 18px;
                                    border-radius: 10px;
                                    border: 1px solid #ddd;
                                }}

                                mark {{
                                    background-color: #fff176;
                                    padding: 3px 5px;
                                    border-radius: 4px;
                                    font-weight: bold;
                                }}
                            </style>
                        </head>
                        <body>
                            {highlighted_text}
                        </body>
                        </html>
                        """

                        render_html_box(highlighted_box, height=350)

                    else:
                        st.info("No highlighted text available.")

                    st.subheader("Matched Sources")

                    matches = result.get("matches", [])

                    if not matches:
                        st.info("No matches found.")

                    for match in matches:

                        st.markdown(f"## {match.get('title', 'No title')}")

                        st.write(
                            "**Similarity:**",
                            f"{match.get('similarity', 0)}%"
                        )

                        st.write(
                            "**Matched Against:**",
                            match.get("matched_against", "")
                        )

                        st.write(
                            "**Authors:**",
                            ", ".join(match.get("authors", []))
                            if match.get("authors")
                            else "Not available"
                        )

                        st.write(
                            "**Journal:**",
                            match.get("journal", "Not available")
                        )

                        st.write(
                            "**Type:**",
                            match.get("type", "Not available")
                        )

                        st.write(
                            "**DOI:**",
                            match.get("doi", "Not available")
                        )

                        if match.get("filename"):
                            st.write(
                                "**Filename:**",
                                match.get("filename")
                            )

                        if match.get("url"):
                            st.markdown(
                                f"[Open Source]({match.get('url')})"
                            )

                        matched_sentences = match.get("matched_sentences", [])

                        if matched_sentences:
                            st.markdown("### Sentence-Level Matches")

                            for sentence_match in matched_sentences:

                                user_sentence = safe_html(
                                    sentence_match.get("user_sentence", "")
                                )

                                source_sentence = safe_html(
                                    sentence_match.get("source_sentence", "")
                                )

                                similarity = sentence_match.get(
                                    "weighted_similarity",
                                    0
                                )
                                raw_similarity = sentence_match.get(
                                    "similarity",
                                    0
                                )
                                source_field = sentence_match.get(
                                    "source_field",
                                    "source"
                                )
                                match_type = safe_html(
                                    sentence_match.get(
                                        "match_type",
                                        "Similarity Match"
                                    )
                                )
                                fuzzy_similarity = sentence_match.get(
                                    "fuzzy_similarity",
                                    0
                                )
                                lexical_overlap = sentence_match.get(
                                    "lexical_overlap",
                                    0
                                )
                                card_color = sentence_match.get(
                                    "highlight_color",
                                    "#fff3cd"
                                )
                                border_color = sentence_match.get(
                                    "border_color",
                                    "#ffc107"
                                )

                                html_content = f"""
                                <html>
                                <head>
                                    <style>
                                        body {{
                                            font-family: Arial, sans-serif;
                                            background-color: {card_color};
                                            padding: 14px;
                                            border-radius: 8px;
                                            border-left: 5px solid {border_color};
                                            color: #111;
                                            line-height: 1.7;
                                        }}

                                        .label {{
                                            font-weight: bold;
                                            margin-bottom: 5px;
                                        }}

                                        .section {{
                                            margin-bottom: 15px;
                                        }}
                                    </style>
                                </head>

                                <body>
                                    <div class="section">
                                        <div class="label">Match type:</div>
                                        <div>{match_type}</div>
                                    </div>

                                    <div class="section">
                                        <div class="label">Your text:</div>
                                        <div>{user_sentence}</div>
                                    </div>

                                    <div class="section">
                                        <div class="label">Matched source text:</div>
                                        <div>{source_sentence}</div>
                                    </div>

                                    <div class="section">
                                        <div class="label">Weighted Similarity:</div>
                                        <div>{similarity}% from {source_field}</div>
                                    </div>

                                    <div class="section">
                                        <div class="label">Raw Sentence Similarity:</div>
                                        <div>{raw_similarity}%</div>
                                    </div>

                                    <div class="section">
                                        <div class="label">Fuzzy / Word Overlap:</div>
                                        <div>{fuzzy_similarity}% / {lexical_overlap}%</div>
                                    </div>
                                </body>
                                </html>
                                """

                                render_html_box(html_content, height=260)

                        else:
                            st.info(
                                "No strong sentence-level matches found for this source."
                            )

                        st.divider()

            except requests.exceptions.ConnectionError:
                st.error(
                    "Could not connect to the FastAPI backend. "
                    "Make sure it is running with: uvicorn app.main:app --reload"
                )

            except Exception as error:
                st.error(f"Something went wrong: {error}")
