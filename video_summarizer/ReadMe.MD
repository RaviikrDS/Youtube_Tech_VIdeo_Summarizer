# 🎥 AI-Powered Video Summarizer

The **AI-Powered Video Summarizer** is a Streamlit-based application that intelligently summarizes educational and technical videos. It extracts key concepts, provides clean code snippets, and organizes insights into structured documentation — all using Google Gemini models.

---

## 🧠 Key Features

- Extracts and summarizes transcripts from technical/coding videos.
- Outputs detailed summaries with proper headings and code formatting.
- Generates clean documentation in:
  - 🌐 `.html` (Web Page)
- Custom prompt system optimized for coding and technical breakdowns.
- Works with **Google Gemini API** (v1beta via `google.generativeai`).

---

## 📁 Project Folder Structure

```

VideoSummarizer\_Project/
│
├── video_summarizer/
│   ├── app.py                  # Main Streamlit App        
│   ├── requirements.txt           # All dependencies
│   ├── output/                    # Stores generated files (txt, html, docx)
│   └── .env                       # API keys and config variables
│
├── README.md                      # Project overview and instructions
└── venv/                          # Virtual Environment

````

---

## ⚙️ Setup Instructions

### 1. Clone the Repository


### 2. Create and Activate Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure API (Google Gemini)

1. **Install Google Generative AI SDK:**

   ```bash
   pip install google-generativeai
   ```

2. **Get Your Gemini API Key:**

   * Visit: [https://makersuite.google.com/app/apikey]
   * Copy your API key.

3. **Set Up Environment File (.env):**

   Create a `.env` file inside `video_summarizer/` directory:

   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

---

## 🚀 Run the App

Use Streamlit to launch the app:

```bash
streamlit run app_v1.py
```

This will open the app in your browser at [http://localhost:8501]

---

## ✅ Output Files

After summarization, the app allows downloading the result as:

* `.html` → Professional web-like documentation with syntax highlighting



## TODO / Future Enhancements

* Video upload and auto-transcription integration
* Support for multiple LLMs (e.g., OpenAI, Claude)
* Topic filtering and tagging system
* Multiple language support

---

## Contributing

Feel free to fork the project and submit PRs! Suggestions welcome via Issues.

