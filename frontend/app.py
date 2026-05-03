import streamlit as st
import requests


API_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="AI Plagiarism Checker",
    page_icon="📝",
    layout="wide"
)


st.title("📝 AI Plagiarism Checker")
st.write("Upload an assignment or paste text to check similarity against reference documents.")


st.sidebar.header("Reference Sources")

try:
    sources_response = requests.get(f"{API_URL}/sources")

    if sources_response.status_code == 200:
        sources_data = sources_response.json()
        st.sidebar.write(f"Total Sources: {sources_data['total_sources']}")

        for source in sources_data["sources"]:
            st.sidebar.write(f"- {source}")
    else:
        st.sidebar.error("Could not load sources.")

except Exception:
    st.sidebar.error("Backend is not running.")


st.subheader("Upload Assignment File")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["txt", "pdf", "docx"]
)


st.subheader("Or Paste Text Directly")

text_input = st.text_area(
    "Paste assignment text here",
    height=250
)


if st.button("Check Plagiarism"):
    if uploaded_file is None and text_input.strip() == "":
        st.warning("Please upload a file or enter text.")

    else:
        with st.spinner("Checking similarity..."):
            try:
                files = None
                data = {}

                if uploaded_file is not None:
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type
                        )
                    }

                if text_input.strip():
                    data["text"] = text_input

                response = requests.post(
                    f"{API_URL}/check",
                    files=files,
                    data=data
                )

                if response.status_code == 200:
                    result = response.json()

                    if "error" in result:
                        st.error(result["error"])

                    else:
                        overall_score = result["overall_similarity"]

                        st.subheader("Overall Similarity Score")
                        st.progress(overall_score / 100)
                        st.metric("Similarity", f"{overall_score}%")

                        if overall_score >= 70:
                            st.error("High similarity detected.")
                        elif overall_score >= 40:
                            st.warning("Moderate similarity detected.")
                        else:
                            st.success("Low similarity detected.")

                        st.subheader("Top Matched Sources")

                        for match in result["top_matches"]:
                            with st.expander(
                                f"{match['filename']} - {match['combined_similarity']}%"
                            ):
                                st.write(f"TF-IDF Similarity: {match['tfidf_similarity']}%")
                                st.write(f"Embedding Similarity: {match['embedding_similarity']}%")
                                st.write(f"Combined Similarity: {match['combined_similarity']}%")

                        st.subheader("Highlighted Submitted Text")

                        st.markdown(
                            """
                            <div style="margin-bottom:10px;">
                                <span style="background-color:#ffb3b3; padding:4px; border-radius:4px;">Direct Similarity</span>
                                <span style="background-color:#fff3b0; padding:4px; border-radius:4px;">Possible Paraphrase</span>
                                <span style="background-color:#cce5ff; padding:4px; border-radius:4px;">Moderate Similarity</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        highlighted_text = result.get("highlighted_text", "")

                        st.markdown(
                            f"""
                            <div style="
                                border:1px solid #ddd;
                                border-radius:8px;
                                padding:15px;
                                line-height:1.8;
                                background-color:#fafafa;
                                color:#000000;
                            ">
                                {highlighted_text}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        st.subheader("Matched Sentences / Phrases")

                        if result["matched_sentences"]:
                            for sentence_match in result["matched_sentences"]:
                                st.markdown("---")

                                match_type = sentence_match.get("match_type", "Similarity Match")
                                similarity = sentence_match["similarity"]

                                if match_type == "Direct Similarity":
                                    st.error(f"{match_type} — {similarity}%")
                                elif match_type == "Possible Paraphrase":
                                    st.warning(f"{match_type} — {similarity}%")
                                elif match_type == "Moderate Similarity":
                                    st.info(f"{match_type} — {similarity}%")
                                else:
                                    st.write(f"{match_type} — {similarity}%")

                                st.write(f"Source: **{sentence_match['source']}**")

                                st.markdown("Submitted Sentence:")
                                st.warning(sentence_match["uploaded_sentence"])

                                st.markdown("Matched Reference Sentence:")
                                st.info(sentence_match["matched_sentence"])
                        else:
                            st.write("No strong sentence-level matches found.")

                else:
                    st.error("Something went wrong with the backend request.")

            except Exception as e:
                st.error(f"Error: {e}")