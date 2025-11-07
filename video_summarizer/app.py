import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import tempfile
import re
import html

# =========================
# 🌟 INITIAL SETUP
# =========================
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Chinese": "zh",
    "Japanese": "ja",
    "Russian": "ru",
    "Portuguese": "pt",
    "Arabic": "ar"
}

st.set_page_config(
    page_title="TubeNotes AI",
    layout="wide",
    page_icon="📒",
    initial_sidebar_state="expanded"
)

# =========================
# 🎨 SIDEBAR UI
# =========================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/5968/5968705.png", width=80)
    st.markdown("<h2 style='color:#8B8B00;'>Video Summarizer</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:16px;color:#444;'>Summarize YouTube programming, AI/ML, and software development videos into developer-friendly notes in your preferred language.</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")
    st.markdown("**Select Output Language:**")
    selected_language = st.selectbox(
        "Language",
        options=list(LANGUAGES.keys()),
        index=0,
        key="language_selector"
    )
    st.markdown("---")
    st.markdown(
        "<small style='color:#888;'>Powered by Google Gemini | Developed by Your Team</small>",
        unsafe_allow_html=True
    )

# =========================
# 🎓 MAIN PAGE HEADER
# =========================
st.markdown(
    "<h1 style='color:#003366;text-align:center;'>🎓 YouTube Video Summarizer</h1>",
    unsafe_allow_html=True
)

# =========================
# 🔗 YOUTUBE LINK INPUT
# =========================
youtube_link = st.text_input("🔗 Enter YouTube Video Link:", key="youtube_link_input")

def get_video_id(url):
    """Extract YouTube video ID from link."""
    try:
        if "youtu.be" in url:
            return url.split("/")[-1]
        elif "youtube.com" in url:
            query = urlparse(url).query
            return parse_qs(query)["v"][0]
    except:
        return None
    return None

if youtube_link:
    video_id = get_video_id(youtube_link)
    if video_id:
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)

# =========================
# 🎬 FETCH TRANSCRIPT
# =========================
def extract_transcript_details(youtube_video_url):
    try:
        video_id = get_video_id(youtube_video_url)
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi'])
        transcript = " ".join([entry["text"] for entry in transcript_data])
        return transcript
    except TranscriptsDisabled:
        st.error("Transcripts are disabled for this video.")
        return None
    except Exception as e:
        st.error(f"Error fetching transcript: {e}")
        return None

# =========================
# 🌍 TRANSLATION VIA GEMINI
# =========================
def translate_text(text, target_lang_code):
    if target_lang_code == "en":
        return text
    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        translate_prompt = f"Translate the following technical summary to {target_lang_code} language. Only output the translated text, keeping markdown/code formatting:\n\n{text}"
        response = model.generate_content([translate_prompt])
        return response.text
    except Exception as e:
        st.error(f"Error translating summary: {e}")
        return text

# =========================
# 🤖 GEMINI CONTENT GENERATION
# =========================
def generate_gemini_content(transcript_text, prompt, target_lang_code, progress):
    try:
        progress.progress(40)
        model = genai.GenerativeModel("models/gemini-2.5-flash")

        # Generate Summary
        response = model.generate_content([prompt + transcript_text])
        summary = response.text

        progress.progress(70)
        # Translate (if needed)
        summary = translate_text(summary, target_lang_code)

        progress.progress(100)
        return summary
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        return None

# =========================
# 🧾 MARKDOWN TO HTML
# =========================
def markdown_to_html(md_text):
    md_text = md_text.strip()
    md_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", md_text)
    md_text = re.sub(r"^#{1,3}\s*$", "", md_text, flags=re.MULTILINE)
    md_text = re.sub(r"### (.*?)\n", r"<h2>\1</h2>\n", md_text)

    code_blocks = []

    def replace_code_block(match):
        lang = match.group(1).strip().lower()
        raw_code = match.group(2).strip()
        escaped_code = html.escape(raw_code)
        placeholder = f"[[CODE_BLOCK_{len(code_blocks)}]]"
        code_blocks.append(f'<pre><code class="language-{lang}">{escaped_code}</code></pre>')
        return placeholder

    md_text = re.sub(r"```(\w*)\n(.*?)```", replace_code_block, md_text, flags=re.DOTALL)

    lines = md_text.splitlines()
    processed_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith(("-", "*")):
            processed_lines.append(f"<li>{line.lstrip('-*').strip()}</li>")
        else:
            processed_lines.append(f"<p>{line}</p>")

    html_output = "\n".join(processed_lines)
    for i, block in enumerate(code_blocks):
        html_output = html_output.replace(f"[[CODE_BLOCK_{i}]]", block)

    return html_output

# =========================
# 💾 CREATE HTML FILE
# =========================
def create_html_file(content):
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>AI-Generated Video Summary</title>
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                margin: 40px;
                color: #333;
                background-color: #fafafa;
            }}
            h1 {{
                text-align: center;
                color: #003366;
            }}
            h2 {{
                color: #004488;
                border-bottom: 1px solid #ccc;
                padding-bottom: 5px;
            }}
            pre {{
                background: #f4f4f4;
                padding: 10px;
                border-radius: 8px;
                overflow-x: auto;
            }}
        </style>
    </head>
    <body>
        <h1>📘 AI-Generated Technical Summary</h1>
        {markdown_to_html(content)}
    </body>
    </html>
    """

    file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    with open(file_path.name, "w", encoding="utf-8") as f:
        f.write(html_template)
    return file_path.name

# =========================
# 🚀 MAIN ACTION WITH SPINNER + PROGRESS
# =========================
prompt = "Summarize this transcript into concise, technical bullet points suitable for developer notes:\n\n"

if st.button("📄 Generate Summary", use_container_width=True, key="generate_summary_button"):
    with st.spinner("⏳ Generating your video summary... Please wait!"):
        progress = st.progress(10)
        transcript_text = extract_transcript_details(youtube_link)
        if transcript_text:
            progress.progress(30)
            summary = generate_gemini_content(transcript_text, prompt, LANGUAGES[selected_language], progress)
            if summary:
                st.success("✅ Summary generation complete!")
                st.markdown("<h2 style='color:#007acc;'>📘 AI-Generated Notes:</h2>", unsafe_allow_html=True)
                st.markdown(summary, unsafe_allow_html=True)

                html_path = create_html_file(summary)
                with open(html_path, "rb") as f:
                    st.download_button(
                        f"🖥️ Download Notes as HTML ({selected_language})",
                        f,
                        f"video_summary_{LANGUAGES[selected_language]}.html",
                        mime="text/html",
                        key="download_button"
                    )

                st.info("☁️ Google Drive upload feature coming soon 🚀")
