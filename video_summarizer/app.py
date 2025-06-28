import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import tempfile
import uuid
import re
from docx.shared import Inches, Pt
from docx.enum.section import WD_ORIENT
import html


# Load env variables and configure Gemini
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

prompt = """
You are an expert technical summarizer specializing in educational programming, AI/ML and software development videos.
Your task is to analyze the provided transcript and generate a developer-focused summary that captures all the key concepts, implementations, and code examples explained in the video.

⚙️ Output Requirements:

1. Cover **everything explained or demonstrated** in the video — from theoretical concepts to practical steps.
2. Provide **code snippets exactly as shown or implied**, formatted in correct triple backticks with appropriate language (e.g., ```python, ```bash).
3. Include **step-by-step technical breakdowns** for implementations, setups, or workflows.
4. Mention all **libraries, frameworks, APIs, tools, commands, environments**, or configurations used or referred to.
5. Explain **how and why** certain techniques, code, or tools were used if such reasoning exists in the transcript.
6. Preserve the **logical or chronological flow** of the video so it reads like a structured lesson.
7. Use **markdown formatting** for readability: bold, lists, headings, and sections.

🛑 Do not:
- Add your own interpretation or assume anything not clearly mentioned in the transcript.
- Skip any detail, even if repetitive — be complete.
- break sentence unnecessary. e.g. This code is in requirements.txt: into this code is \n requirements.txt \n :

🛑 Do:
- remove ** from word or sentence and make that word or sentence bold. e.g ** Just example** to Just example in bold letters.
- Use bullet points olny where it is required.
- Optimize the notes based on your understanding without missing any topic.
- Make notes error free in terms of grammar and Punctuations.
- If there is code in notes, at the end proivide full code as well.


📘 Your summary must be formatted like clear developer technical documentation or notes. Use the following structure:

---

### 🔍 Video Summary
Brief summary in 3-5 lines covering the purpose, goals, and output of the video.

### 🧠 Key Concepts
- Bullet points listing all topics, principles, definitions, or ideas explained.

### 💡 Step-by-Step Instructions
- Numbered list of steps followed in the video (e.g., setup, coding, testing, deployment).

### 🧾 Code Snippets
Include all major code shown or described, wrapped in correct ``` code blocks with the language name:
```python
# sample code here

### Conclusion
- Provide very optimize conclusion.
"""

# Extract YouTube video ID
def get_video_id(url):
    try:
        if "youtu.be" in url:
            return url.split("/")[-1]
        elif "youtube.com" in url:
            query = urlparse(url).query
            return parse_qs(query)["v"][0]
    except:
        return None
    return None

# Extract transcript text
def extract_transcript_details(youtube_video_url):
    try:
        video_id = get_video_id(youtube_video_url)
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([entry["text"] for entry in transcript_data])
        return transcript
    except Exception as e:
        st.error(f"Error fetching transcript: {e}")
        return None

# Call Gemini
def generate_gemini_content(transcript_text, prompt):
    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content([prompt + transcript_text])
        return response.text
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        return None


def markdown_to_html(md_text):
    md_text = md_text.strip()

    # --- Convert **bold** syntax into HTML bold ---
    md_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", md_text)

    # --- Remove empty markdown headers like #, ##, ### ---
    md_text = re.sub(r"^#{1,3}\s*$", "", md_text, flags=re.MULTILINE)

    # --- Convert headers ---
    md_text = re.sub(r"### (.*?)\n", r"<h2>\1</h2>\n", md_text)

    # --- Convert fenced code blocks ```language\n...``` ---
    code_blocks = []
    def replace_code_block(match):
        lang = match.group(1)
        code = html.escape(match.group(2).strip())
        placeholder = f"[[CODE_BLOCK_{len(code_blocks)}]]"
        code_blocks.append(f'<pre><code class="language-{lang}">{code}</code></pre>')
        return placeholder

    md_text = re.sub(r"```(\w*)\n(.*?)```", replace_code_block, md_text, flags=re.DOTALL)

    # --- Line-by-line processing for bullets and numbered list ---
    lines = md_text.splitlines()
    processed_lines = []
    in_numbered_list = False
    in_bullets = False

    for line in lines:
        line = line.strip()

        if not line:
            if in_bullets:
                processed_lines.append("</ul>")
                in_bullets = False
            if in_numbered_list:
                processed_lines.append("</ol>")
                in_numbered_list = False
            continue

        # Detect numbered list (e.g., 1. Text)
        if re.match(r"^\d+\.\s", line):
            if not in_numbered_list:
                processed_lines.append("<ol>")
                in_numbered_list = True
            line = re.sub(r"^\d+\.\s*", "", line)
            processed_lines.append(f"<li>{line}</li>")
            continue

        # Detect bullets (* or -), skip if contains bold
        if line.startswith(("-", "*")) and "<strong>" not in line:
            if not in_bullets:
                processed_lines.append("<ul>")
                in_bullets = True
            line = line.lstrip("-*").strip()
            processed_lines.append(f"<li>{line}</li>")
            continue

        if in_bullets:
            processed_lines.append("</ul>")
            in_bullets = False
        if in_numbered_list:
            processed_lines.append("</ol>")
            in_numbered_list = False

        processed_lines.append(f"<p>{line}</p>")

    if in_bullets:
        processed_lines.append("</ul>")
    if in_numbered_list:
        processed_lines.append("</ol>")

    # --- Reinsert code blocks ---
    html_output = "\n".join(processed_lines)
    for i, block in enumerate(code_blocks):
        html_output = html_output.replace(f"[[CODE_BLOCK_{i}]]", block)

    return html_output


def create_html_file(content):
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>AI-Generated Video Summary</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 40px;
                background-color: #fdfdfd;
                color: #333;
                line-height: 1.6;
            }}
            h1 {{
                text-align: center;
                color: #1a1a1a;
                margin-bottom: 40px;
            }}
            h2 {{
                color: #003366;
                margin-top: 30px;
                border-bottom: 2px solid #eee;
                padding-bottom: 5px;
            }}
            ul {{
                margin-left: 30px;
                margin-bottom: 20px;
            }}
            pre {{
                background-color: #f4f4f4;
                padding: 15px;
                border-radius: 8px;
                overflow-x: auto;
                margin-bottom: 20px;
                font-size: 0.95em;
            }}
            code {{
                font-family: Consolas, Monaco, 'Courier New', monospace;
                color: #2c3e50;
            }}
            p {{
                margin-bottom: 10px;
            }}
            .container {{
                max-width: 1000px;
                margin: auto;
                padding: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📘 AI-Generated Technical Summary</h1>
            {markdown_to_html(content)}
        </div>
    </body>
    </html>
    """

    file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    with open(file_path.name, "w", encoding="utf-8") as f:
        f.write(html_template)
    return file_path.name


# Streamlit UI
st.set_page_config(page_title="Video Summarizer", layout="wide")
st.title("🎓 YouTube Technical Video Summarizer with Gemini AI")

youtube_link = st.text_input("🔗 Enter YouTube Video Link:")

if youtube_link:
    video_id = get_video_id(youtube_link)
    if video_id:
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)

if st.button("📄 Generate Summary"):
    transcript_text = extract_transcript_details(youtube_link)

    if transcript_text:
        summary = generate_gemini_content(transcript_text, prompt)
        if summary:
            st.markdown("## 📘 AI-Generated Developer Notes:")
            st.markdown(summary, unsafe_allow_html=True)

            # 📥 HTML (code-highlighted)
            html_path = create_html_file(summary)
            with open(html_path, "rb") as f:
                st.download_button("🖥️ Download as HTML (.html)", f, "video_summary.html", mime="text/html")

            # 🚀 Optional: Upload to Google Drive (placeholder for future)
            if st.checkbox("☁️ Upload to Google Drive (coming soon)", value=False, disabled=True):
                st.info("Google Drive upload will be added in next version.")
