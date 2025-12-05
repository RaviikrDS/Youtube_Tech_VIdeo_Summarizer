import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import tempfile
import re
import html

# Make sure Streamlit listens on the correct port when running on Render
port = int(os.environ.get("PORT", 8501))

# =========================
# INITIAL SETUP
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

# Notes format prompts
NOTES_FORMAT_PROMPTS = {
    "Technical Notes": (                                
        "You are an expert technical summarizer specializing in programming, software development, AI/ML, "
        "Data Scientist, and related technologies.\n\n"
        "Your task is to analyze the transcript and produce comprehensive, developer-focused technical notes "
        "that accurately reflect all concepts, workflows, implementations, and examples described in the video.\n\n"

        "⚙️ Output Requirements:\n"
            "1. Cover all content explained in the video, including theory, implementation steps, workflows, edge cases, and reasoning.\n"
            "2. Clearly mention all libraries, frameworks, APIs, tools, commands, configurations, and environments referenced.\n"
            "3. Provide step-by-step technical breakdowns for setups, integrations, algorithms, or deployments.\n"
            "4. Include code snippets exactly as shown or implied in the transcript, formatted using fenced triple-backtick blocks "
            "   with the appropriate language (e.g., ```python, ```bash, ```javascript).\n"
            "5. Explain the purpose and reasoning behind important techniques, patterns, or architectural decisions when provided.\n"
            "6. Maintain the chronological or logical structure of the video so the notes read like well-organized documentation.\n"
            "7. Use clear Markdown headings, lists, and sub-sections to improve readability.\n"
            "8. When explicitly supported by the transcript, include simple Mermaid diagrams for architecture or process flows, "
            "   wrapped in triple-backtick blocks.\n\n"

        "Do Not:\n"
            "Add or assume information not supported by the transcript.\n"
            "Omit important details, even if repetitive; reorganize them instead of removing them.\n"
            "Introduce awkward sentence breaks or unnatural formatting.\n"
            "Add diagrams that are not directly supported by the content.\n\n"

        "Do:\n"
            "Normalize formatting and use clean Markdown.\n"
            "Use bullet points only when they improve clarity.\n"
            "Reorganize and refine content while preserving every technical detail.\n"
            "Ensure correctness, grammatical quality, and professional writing.\n"
            "If multiple pieces of code appear throughout the transcript, include a 'Full Code' or 'Complete Example' section at the end.\n\n"

        "Structure your output exactly in the following format:\n\n"

        "### Video Summary\n"
        "Provide a 3–5 line overview describing the purpose and goals of the video.\n\n"

        "### Key Concepts\n"
            "Bullet points listing key ideas, definitions, principles, patterns, and technologies discussed.\n\n"

        "### Topic by Topic Analysis\n"
            "1. Sequential, numbered explanations of each workflow, setup step, algorithm, configuration, or implementation "
            "   in the order presented in the video.\n\n"
            "2. Provide Mermaid diagrams only when the transcript clearly supports a visual architecture or process representation.\n\n"
            "3. Explain code with proper comments and explanation\n\n"
        "### Conclusion\n"
            "Write a brief, well-structured conclusion summarizing the technical outcome.\n\n"
        "Transcript:\n\n"
    ),

    # "General Notes Summary": (
    #     "You are a clear, friendly explainer creating structured notes for a general (non-technical) audience.\n\n"
    #     "Your task is to read the transcript and produce a well-organized general summary that captures all key ideas, "
    #     "arguments, examples, and practical advice from the video in simple language.\n\n"
    #     "⚙️ Output Requirements:\n"
    #     "1. Cover all topics discussed in the video, including explanations, examples, stories, and conclusions.\n"
    #     "2. Use plain, accessible language that someone without a technical background can understand.\n"
    #     "3. Group related ideas together under meaningful headings so the notes feel organized, not fragmented.\n"
    #     "4. Use bullet points and numbered lists only where they help clarity and readability.\n"
    #     "5. Maintain the natural flow of the video (introduction → main sections → conclusion).\n"
    #     "6. Do not add your own opinions or assumptions; stay faithful to what the transcript actually says.\n\n"
    #     "🛑 Do not:\n"
    #     "- Introduce new content, opinions, or examples that are not in the transcript.\n"
    #     "- Overload the notes with unnecessary formatting or overly long bullet lists.\n\n"
    #     "✅ Do:\n"
    #     "- Rewrite and organize the content so it is clearer and less repetitive than the raw transcript.\n"
    #     "- Fix grammar and punctuation so the notes read smoothly.\n"
    #     "- Ensure every major topic, subtopic, and example mentioned in the video appears somewhere in the notes.\n\n"
    #     "📘 Structure your output as follows:\n\n"
    #     "### 📺 Video Overview\n"
    #     "A short 3–4 line description of what the video is about, who it is for, and what it covers.\n\n"
    #     "### 🗂️ Main Ideas & Topics\n"
    #     "- Bullet points summarizing the main ideas, themes, and arguments.\n\n"
    #     "### 🧩 Important Details & Examples\n"
    #     "- Briefly describe any important explanations, stories, demonstrations, or case studies from the video.\n\n"
    #     "### ✅ Practical Takeaways\n"
    #     "- List the key lessons, suggestions, or action points that viewers can apply.\n\n"
    #     "### 🧾 Summary in One Paragraph\n"
    #     "A final, concise paragraph that wraps up the entire video in simple terms.\n\n"
    #     "Transcript:\n\n"
    # ),

    # "Coding Notes Summary": (
    #     "You are a senior software engineer documenting a programming or coding tutorial.\n\n"
    #     "Your task is to analyze the transcript and create precise, implementation-oriented coding notes that include all "
    #     "code, commands, and step-by-step guidance shown in the video.\n\n"
    #     "⚙️ Output Requirements:\n"
    #     "1. Capture every important coding action: file creation, function/class definitions, configuration changes, commands, and tests.\n"
    #     "2. Include all code snippets exactly as described or shown, formatted using fenced code blocks with the correct language "
    #     "(for example, ```python, ```javascript, ```bash, ```html).\n"
    #     "3. Preserve the order of development: setup → core implementation → enhancements → testing/debugging → final result.\n"
    #     "4. Mention all tools, libraries, frameworks, packages, versions, and environment details that appear in the transcript.\n"
    #     "5. When the transcript explains why something is done a certain way, include that reasoning briefly.\n"
    #     "6. If multiple files or components are involved, clearly separate sections by file or component name.\n"
    #     "7. Optionally use simple Mermaid diagrams for data flow, component interactions, or architecture if these flows are clearly "
    #     "shown in the transcript.\n\n"
    #     "🛑 Do not:\n"
    #     "- Invent code that is not supported by the transcript.\n"
    #     "- Change the meaning or intent of the demonstrated code.\n"
    #     "- Omit small but important details like flags, parameters, or file paths.\n\n"
    #     "✅ Do:\n"
    #     "- Clean up minor transcript artifacts (like stray `**` or broken lines) while keeping the code logically identical.\n"
    #     "- Ensure the final notes could be used by a developer to reproduce the demo or project from scratch.\n"
    #     "- At the end, if the tutorial builds up a final program or project, provide a \"Full Code\" section with the complete code "
    #     "assembled in one place.\n\n"
    #     "📘 Structure your output as follows:\n\n"
    #     "### 🔍 Video Summary\n"
    #     "A 2–4 line explanation of what is being built or demonstrated and with which technologies.\n\n"
    #     "### 🧠 Key Concepts & Setup\n"
    #     "- List the core ideas (patterns, paradigms, or techniques) and any setup steps (requirements, installations, environment).\n\n"
    #     "### 💻 Implementation Steps\n"
    #     "1. Numbered, step-by-step description of how the code is written or modified during the video.\n\n"
    #     "### 🧾 Code Snippets by Section\n"
    #     "- Show code snippets grouped by file, component, or logical section, using proper fenced code blocks.\n\n"
    #     "### 🧩 Debugging / Testing (if any)\n"
    #     "- Summarize how issues are identified and fixed, and how the code is tested.\n\n"
    #     "### 🧱 Full Code (if reconstructable)\n"
    #     "- Provide the complete final code or main files as described in the video.\n\n"
    #     "### ✅ Conclusion\n"
    #     "- Briefly summarize what the viewer is able to build or understand after following the tutorial.\n\n"
    #     "Transcript:\n\n"
    # ),

    # "Research Notes Summary": (
    #     "You are an analytical research assistant creating structured, research-style notes from the transcript.\n\n"
    #     "Your task is to extract and organize all important information related to research questions, background, methods, "
    #     "evidence, results, and interpretations presented in the video.\n\n"
    #     "⚙️ Output Requirements:\n"
    #     "1. Identify the main topic or research question the video addresses.\n"
    #     "2. Capture any theoretical background, literature references, or conceptual frameworks discussed.\n"
    #     "3. Summarize methods, experiments, datasets, models, or analytical approaches mentioned.\n"
    #     "4. Clearly list key findings, insights, or results, including any quantitative metrics cited.\n"
    #     "5. Note strengths, limitations, assumptions, and open questions if they appear in the transcript.\n"
    #     "6. Maintain a neutral, objective tone appropriate for academic or research notes.\n"
    #     "7. Where suitable and clearly supported by the transcript, use Mermaid diagrams to represent processes, pipelines, or "
    #     "comparisons (for example, experimental workflows or model pipelines).\n\n"
    #     "🛑 Do not:\n"
    #     "- Add your own hypotheses, interpretations, or speculative commentary.\n"
    #     "- Invent numbers, results, or citations that are not provided.\n\n"
    #     "✅ Do:\n"
    #     "- Reorganize the raw spoken content into a clean, logical research structure.\n"
    #     "- Fix grammar and punctuation for clarity, while preserving the original meaning.\n"
    #     "- Ensure that all key points, arguments, and examples from the transcript appear somewhere in the notes.\n\n"
    #     "📘 Structure your output as follows:\n\n"
    #     "### 📚 Overview & Research Question\n"
    #     "- Briefly describe the main topic and central question or problem being discussed.\n\n"
    #     "### 🧩 Background & Context\n"
    #     "- Summarize any theoretical background, prior work, or context needed to understand the topic.\n\n"
    #     "### 🧪 Method / Approach\n"
    #     "- Describe the methods, models, experiments, datasets, or procedures mentioned.\n\n"
    #     "### 📊 Key Findings / Insights\n"
    #     "- Bullet points listing the main results, observations, or insights from the video.\n\n"
    #     "### ⚖️ Strengths, Limitations & Assumptions\n"
    #     "- Summarize any pros/cons, caveats, or assumptions explicitly discussed.\n\n"
    #     "### 🔭 Open Questions / Future Directions\n"
    #     "- List any future work, unanswered questions, or directions suggested.\n\n"
    #     "### ✅ Takeaway Summary\n"
    #     "A concise paragraph summarizing the overall message or implications of the video.\n\n"
    #     "Transcript:\n\n"
    # ),

    # "Short Summary": (
    #     "You are summarizing the transcript into a very short, high-signal overview that still covers all major topics.\n\n"
    #     "Your task is to compress the content into a compact form while preserving the core ideas and outcomes of the video.\n\n"
    #     "⚙️ Output Requirements:\n"
    #     "1. Capture the main topic, goal, and key ideas of the video without going into fine-grained detail.\n"
    #     "2. Do not exceed 5–8 bullet points OR 1–2 short paragraphs (choose whichever fits the content best).\n"
    #     "3. Use simple, direct language so the summary can be read and understood quickly.\n"
    #     "4. Include only the most important concepts, decisions, or results — no filler.\n"
    #     "5. Do not introduce new information that is not present in the transcript.\n\n"
    #     "🛑 Do not:\n"
    #     "- Add diagrams, long explanations, or detailed step-by-step instructions.\n"
    #     "- Use very long sentences or nested lists.\n\n"
    #     "✅ Do:\n"
    #     "- Make the summary grammatically correct and easy to scan.\n"
    #     "- Ensure that every major section or turning point in the video is reflected at least once.\n\n"
    #     "📘 Structure your output as one of the following (choose the best fit based on the transcript):\n\n"
    #     "Option A – Bulleted Summary:\n"
    #     "- 5–8 concise bullet points covering what the video explains, demonstrates, or concludes.\n\n"
    #     "Option B – Paragraph Summary:\n"
    #     "1–2 short paragraphs that describe the core idea, what is done or shown, and the final takeaway.\n\n"
    #     "Transcript:\n\n"
    # ),

    # "UPSC Preparation Format": (
    #     "You are an expert UPSC mentor and content curator. Your task is to convert the transcript into high-quality, "
    #     "exam-oriented notes suitable for UPSC (Civil Services) preparation.\n\n"
    #     "⚙️ Output Requirements:\n"
    #     "1. Identify all topics, subtopics, and dimensions (historical, geographical, economic, social, political, ethical, etc.) "
    #     "relevant for UPSC GS papers, Essay, or optional subjects.\n"
    #     "2. Extract only the points that are conceptually important, factually relevant, or analytically useful for mains and prelims.\n"
    #     "3. Highlight important keywords, terms, committees, schemes, institutions, reports, and constitutional / legal provisions.\n"
    #     "4. For each important keyword, provide:\n"
    #     "   - A short definition/meaning in simple terms.\n"
    #     "   - 2–4 useful synonyms or related phrases (only if they make sense in the given context).\n"
    #     "5. Avoid unnecessary storytelling; focus on crisp, point-wise content that can be revised quickly.\n"
    #     "6. Maintain factual accuracy; do not invent data, reports, or case laws that are not clearly present in the transcript.\n"
    #     "7. Use neutral, exam-style language — clear, balanced, and free from ideological bias.\n\n"
    #     "🛑 Do not:\n"
    #     "- Add external facts, statistics, or articles that are not mentioned or clearly implied by the transcript.\n"
    #     "- Turn the notes into long paragraphs without structure.\n"
    #     "- Use casual or conversational tone.\n\n"
    #     "✅ Do:\n"
    #     "- Reorganize the content logically (issue → causes → impact → measures → way forward) wherever applicable.\n"
    #     "- Fix grammar and punctuation so that the notes are ready to be used in answers.\n"
    #     "- Ensure coverage of all major aspects discussed in the video.\n\n"
    #     "📘 Structure your output exactly as follows:\n\n"
    #     "### 📌 Topic & Relevance for UPSC\n"
    #     "- 2–4 lines explaining what the topic is and where it fits in the UPSC syllabus (e.g., GS2 – Polity & Governance).\n\n"
    #     "### 🧠 Core Concepts & Definitions\n"
    #     "- Bullet points explaining all key concepts in simple, precise language.\n\n"
    #     "### 📊 Important Points / Dimensions\n"
    #     "- Point-wise coverage of all major dimensions (historical, constitutional, economic, social, environmental, ethical, etc.).\n\n"
    #     "### 🔑 Keywords, Meanings & Synonyms\n"
    #     "- For each important keyword from the transcript:\n"
    #     "  - **Keyword** – short meaning / definition.\n"
    #     "  - Synonyms / related keywords: A, B, C (only if meaningful).\n\n"
    #     "### 🧩 Examples, Case Studies or Illustrations (if any)\n"
    #     "- Briefly list any examples, case studies, or real-world references mentioned.\n\n"
    #     "### 🧭 Way Forward / Policy Suggestions (only if present in transcript)\n"
    #     "- Summarize any suggestions, reforms, or recommendations discussed.\n\n"
    #     "### ✅ UPSC-Style Conclusion\n"
    #     "- 1–2 well-crafted, exam-oriented concluding paragraphs that connect the topic to larger constitutional values, "
    #     "governance, sustainable development, or ethical considerations — strictly based on the transcript.\n\n"
    #     "Transcript:\n\n"
    # ),

    "Interview QnA Notes": (
        "You are an experienced interviewer for mid-senior AI/ML and Data Science roles (~5 years experience).\n\n"
        "Convert the transcript into **interview-oriented preparation notes** containing realistic, high-quality "
        "questions and structured answers strictly based on the video content.\n\n"
        
        "⚙️ Output Requirements:\n"
        "1. Extract all relevant concepts, tools, techniques, workflows, and trade-offs discussed in the transcript.\n"
        "2. Generate interview questions that a mid-senior AI/ML or Data Science candidate would typically face, "
            "based only on the transcript topics.\n"
        "3. Provide clear, concise, technically accurate answers grounded strictly in the transcript "
            "(paraphrased and organized, no external content).\n"
        "4. Include a balanced mix of:\n"
            " Conceptual questions (What, Why)\n"
            " Practical/scenario questions (How would you…)\n"
            " Implementation questions (architecture, modeling, evaluation, deployment)\n"
            " Workflow / pipeline reasoning\n"
        "5. Use language appropriate for a 5-year experienced candidate; answers should be structured and speak-ready.\n\n"
        
        "🛑 Do Not:\n"
            "  Introduce external information, tools, or architectures not present or implied.\n"
            "  Add generic interview questions unrelated to the transcript.\n"
            "  Hallucinate metrics or technical details.\n\n"
        
        "✅ Do:\n"
        "- Rephrase transcript content into strong interview-style Q&A.\n"
        "- Emphasize reasoning, trade-offs, advantages, disadvantages, and decision-making when provided.\n"
        "- Ensure grammar and clarity suitable for verbal interviews.\n\n"

        "📘 Structure your output as follows:\n\n"

        "### Overview\n"
        "2–4 lines summarizing which AI/ML/Data Science interview domains this topic prepares the candidate for.\n\n"

        "### Core Concepts to Know\n"
            "Bullet points listing the key concepts, tools, workflows, and principles covered in the video.\n\n"

        "### Most Asked Interview Questions (Based on This Topic)\n"
            "Extract and generate the **most commonly asked questions** from this domain, strictly based on the transcript.\n"
            "Around 5–10 high-frequency or high-importance questions.\n"
            "Provide **short, sharp answers** based entirely on the transcript.\n\n"

        "### Main Interview Questions & Answers\n"
        "Q1: <High-quality question derived from transcript>\n"
         "Ans: <Clear, structured answer based only on the transcript>\n\n"

        "Q2: …\n"
        "Q3: …\n"
        "(Include as many meaningful Q&A pairs as the transcript supports.)\n\n"

        "### Scenario Based Questions\n"
        "- 2–5 scenario-based or problem-solving questions relevant to the transcript/topic.\n"
        "- Provide practical, real senario, structured answers grounded in the transcript.\n\n"

        "### Final Interview Tips (Based on This Video)\n"
        "   3–6 bullet points summarizing how the candidate can leverage the video's content to answer AI/ML/Data Science "
        "   interview questions confidently at a mid-senior level.\n\n"

        "Transcript:\n\n"
    )
}


st.set_page_config(
    page_title="TubeNotes AI",
    layout="wide",
    page_icon="📝",
    initial_sidebar_state="expanded"
)

# =========================
# SIDEBAR UI
# =========================
with st.sidebar:
    st.image("logo.png", width=100)
    st.markdown("<h2 style='color:#8B8B00;'>TubeNotes AI </h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:16px; color:#888; font-style:italic;'> Tubenotes AI transforms YouTube video content into concise, organized notes using advanced AI. Save time, improve retention, and turn any YouTube video into actionable insights in your preferred language. </p>",
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.markdown("**Select Your Preferred Language for Notes:**")
    selected_language = st.selectbox(
        "Language",
        options=list(LANGUAGES.keys()),
        index=0,
        key="language_selector"
    )
    st.markdown("---")
    st.markdown(
        "<small style='color:#888;'>Powered by Google Gemini | Developed by Ravi</small>",
        unsafe_allow_html=True
    )

# =========================
# MAIN PAGE HEADER
# =========================
st.markdown(
    "<h1 style='color:#CCCCCC;text-align:center;'>📝 TubeNotes AI </h1>",
    unsafe_allow_html=True
)

# =========================
# YOUTUBE LINK INPUT
# =========================
youtube_link = st.text_input("🔗 Enter YouTube Video Link:", placeholder=" Paste your YouTube link here...", key="youtube_link_input")

# =========================
# NOTES FORMAT DROPDOWN + CUSTOM PROMPT
# =========================

notes_options = ["Choose the format for your notes..."] + list(NOTES_FORMAT_PROMPTS.keys()) + ["Custom Prompt"]

selected_notes_format = st.selectbox(
    "🧾 Notes Format",
    options=notes_options,
    index=0,
    key="notes_format_selector"
)

# Prevent generating summary if placeholder is selected
if selected_notes_format == "Choose the format for your notes...":
    st.warning("Please select a notes format to continue.")


custom_prompt_text = None
if selected_notes_format == "Custom Prompt":
    custom_prompt_text = st.text_area(
        "✍️ Write your custom prompt here:",
        placeholder=(
            "Example: Create detailed lecture-style notes with headings, subheadings, bullet points, "
            "and clear explanations. Include key definitions, examples, and summary at the end."
        ),
        height=200
    )

notes_name = st.text_input(
    "Enter the Notes Name:",
    placeholder="Write your Notes Name",
    key="notes_name"
)


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
# FETCH TRANSCRIPT
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
# TRANSLATION VIA GEMINI
# =========================
def translate_text(text, target_lang_code):
    if target_lang_code == "en":
        return text
    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        # Generic translation prompt for all note types
        translate_prompt = (
            f"Translate the following notes into the target language. Preserve any code blocks and "
            f"markdown formatting.\n"
            f"Target language code: {target_lang_code}\n\n"
            f"Notes:\n{text}"
        )
        response = model.generate_content([translate_prompt])
        return response.text
    except Exception as e:
        st.error(f"Error translating summary: {e}")
        return text

# =========================
# GEMINI CONTENT GENERATION
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
# MARKDOWN TO HTML
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
# CREATE HTML FILE
# =========================
def create_html_file(content, header_title="📝 TubeNotes AI"):
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>📝 TubeNotes AI</title>
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
        <h1>{header_title}</h1>
        {markdown_to_html(content)}
    </body>
    </html>
    """

    file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    with open(file_path.name, "w", encoding="utf-8") as f:
        f.write(html_template)
    return file_path.name

# =========================
# MAIN ACTION WITH SPINNER + PROGRESS
# =========================
file_name = f"{notes_name or 'video_summary'}.html"
if st.button("📄 Generate Notes", use_container_width=True, key="generate_summary_button"):
    if not youtube_link:
        st.error("Please enter a YouTube video link first.")
        st.stop()

    # 🚨 Guard against placeholder selection
    if selected_notes_format == "Choose the format for your notes...":
        st.error("Please select a valid notes format before generating.")
        st.stop()

    with st.spinner("⏳ Generating your video summary... Please wait!"):
        progress = st.progress(10)
        transcript_text = extract_transcript_details(youtube_link)
        if transcript_text:
            progress.progress(30)

            # Decide prompt based on selected format
            if selected_notes_format == "Custom Prompt":
                if not custom_prompt_text:
                    st.error("Please enter your custom prompt before generating notes.")
                    st.stop()
                prompt = custom_prompt_text.strip() + "\n\nTranscript:\n\n"
                html_header_title = "📘 Custom Prompt Notes"
            else:
                # Extra safety: ensure key exists
                if selected_notes_format not in NOTES_FORMAT_PROMPTS:
                    st.error("Invalid notes format selected. Please try again.")
                    st.stop()

                prompt = NOTES_FORMAT_PROMPTS[selected_notes_format]
                html_header_title = f"📘 {selected_notes_format}"

            summary = generate_gemini_content(
                transcript_text,
                prompt,
                LANGUAGES[selected_language],
                progress
            )

            if summary:
                st.success("Notes generation complete!")
                st.markdown(
                    f"<h2 style='color:#007acc;'>📝 TubeNotes AI ({selected_notes_format}):</h2>",
                    unsafe_allow_html=True
                )
                st.markdown(summary, unsafe_allow_html=True)

                html_path = create_html_file(summary, header_title=html_header_title)
                with open(html_path, "rb") as f:
                    st.download_button(
                        f"🖥️ Download Notes as HTML ({selected_language})",
                        f,
                        file_name,
                        mime="text/html",
                        key="download_button"
                    )

                st.info("☁️ Google Drive upload feature coming soon 🚀")
                st.info(" Multiple Notes Format feature coming soon 🚀")
                st.info(" Notes Backup feature coming soon 🚀")
