# YouTube Community Quiz Generator

An automated AI tool that turns your latest YouTube videos into engaging **YouTube Community Quiz Posts**, featuring a streamlined **Gradio Web UI** for reviewing, editing, and copying quizzes.

---

## 🌟 Key Features

- **Latest Video Retrieval:** Fetches the 10 most recent uploads from any YouTube channel handle or ID via the official YouTube Data API v3 and automatically selects a random video (with manual dropdown selection).
- **Transcript Extraction & Local Caching:** Downloads video transcripts using `youtube-transcript-api` and caches them locally to avoid redundant API calls.
- **AI-Powered Quiz Generation:** Analyzes transcript content using OpenRouter LLMs (defaulting to fast models like `google/gemini-2.5-flash`) with strict prompt constraints (4 options, ≤ 80 characters per option, concise explanations).
- **Bias Prevention & Link Integration:** Automatically shuffles options to eliminate positional bias (e.g. Option B always correct) and appends the video URL directly to the question for viewer engagement.
- **Review & Edit UI:** Modern Gradio dark theme interface allowing you to easily review and refine the generated question, options, correct answer, and explanation before sharing.
- **Turnkey Free Cloud Hosting:** Pre-configured with `app.py` and `requirements.txt` for 1-click free 24/7 deployment on Hugging Face Spaces or Render.

---

## 📁 Project Structure

```
Youtube-Quiz-Generator/
├── app/
│   ├── config/
│   │   └── settings.py          # App settings & env configuration
│   ├── quiz/
│   │   ├── generator.py         # Quiz generation pipeline & bias shuffle
│   │   ├── models.py            # Pydantic Quiz models
│   │   ├── prompts.py           # LLM prompt templates
│   │   ├── validator.py         # Quiz validation rules
│   │   └── providers/
│   │       └── openrouter.py    # OpenRouter API client
│   ├── ui/
│   │   ├── components.py        # Custom styling & formatting
│   │   └── gradio_app.py        # Gradio Blocks UI definition
│   ├── utils/
│   │   └── logger.py            # Logging setup
│   ├── youtube/
│   │   ├── api.py               # YouTube Data API v3 client
│   │   ├── transcript.py        # Transcript manager with caching
│   │   └── videos.py            # Video selection logic
│   └── main.py                  # Main Gradio application entrypoint
├── app.py                       # Root launcher for Hugging Face Spaces
├── main.py                      # Local root launcher
├── pyproject.toml               # Project metadata & dependencies
├── requirements.txt             # Standard pip requirements for cloud hosting
└── tests/                       # Unit & integration test suite
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or standard `pip`

### 2. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Configure your API keys in `.env`:

```env
# OpenRouter API Key (for LLM quiz generation)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=google/gemini-2.5-flash

# YouTube Data API v3 Key
YOUTUBE_API_KEY=your_youtube_api_key_here

# Default YouTube Channel Handle or ID (optional)
YOUTUBE_CHANNEL_ID=@YourChannel
```

### 3. Run Locally

With **uv**:
```bash
uv run python -m app.main
```

Or with standard Python / venv:
```bash
pip install -r requirements.txt
python main.py
```

Open your browser to: [http://127.0.0.1:7860](http://127.0.0.1:7860)

---

## 🌐 Free Cloud Hosting (Hugging Face Spaces)

This repository includes `app.py` and `requirements.txt`, making it ready for **free 24/7 hosting on Hugging Face Spaces**:

1. Go to [huggingface.co](https://huggingface.co) and sign in.
2. Click **New Space** → Give it a name (e.g., `youtube-quiz-generator`).
3. Select **Gradio** as the Space SDK and choose **CPU Basic (Free)**.
4. Push or connect this GitHub repository to the Space.
5. In your Space's **Settings** → **Variables and secrets**, add your secrets:
   - `OPENROUTER_API_KEY`
   - `YOUTUBE_API_KEY`
   - `YOUTUBE_CHANNEL_ID` *(optional)*
6. Hugging Face will automatically build and host the app with a permanent public URL!

---

## 🧪 Running Tests

Run the full test suite using `pytest`:

```bash
uv run pytest
```
