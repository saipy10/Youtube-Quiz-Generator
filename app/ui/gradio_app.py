import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import gradio as gr

from app.config.settings import settings
from app.youtube.api import YouTubeAPI
from app.youtube.videos import Video, select_random_video
from app.youtube.transcript import TranscriptManager
from app.quiz.generator import QuizGenerator, format_question_with_video_link
from app.quiz.models import Quiz
from app.quiz.validator import validate_quiz_inputs, ValidationResult
from app.ui.components import CUSTOM_CSS, format_video_markdown
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

QUIZZES_DIR = settings.DATA_DIR / "quizzes"
QUIZZES_DIR.mkdir(parents=True, exist_ok=True)


def get_channel_posts_url(channel_input: str) -> str:
    """Constructs the canonical channel community/posts URL."""
    cid = (channel_input or settings.YOUTUBE_CHANNEL_ID or "").strip()
    if not cid:
        return "https://www.youtube.com"

    if "youtube.com" in cid:
        if not cid.endswith("/posts"):
            cid = cid.rstrip("/") + "/posts"
        return cid

    if cid.startswith("UC"):
        return f"https://www.youtube.com/channel/{cid}/posts"
    elif cid.startswith("@"):
        return f"https://www.youtube.com/{cid}/posts"
    else:
        return f"https://www.youtube.com/channel/{cid}/posts"


def format_plaintext_quiz(quiz_dict: dict) -> str:
    """Formats quiz for clean, single-click copy-pasting."""
    q = quiz_dict.get("question", "")
    opts = quiz_dict.get("options", ["", "", "", ""])
    correct_idx = quiz_dict.get("correct_answer", 0)
    exp = quiz_dict.get("explanation", "")
    labels = ["A", "B", "C", "D"]
    corr_letter = labels[correct_idx] if 0 <= correct_idx < 4 else "A"

    return (
        f"QUESTION:\n{q}\n\n"
        f"ANSWERS:\n"
        f"Answer 1: {opts[0]}\n"
        f"Answer 2: {opts[1]}\n"
        f"Answer 3: {opts[2]}\n"
        f"Answer 4: {opts[3]}\n\n"
        f"CORRECT ANSWER: Option {corr_letter} ({opts[correct_idx]})\n\n"
        f"EXPLANATION:\n{exp}"
    )


def create_app() -> gr.Blocks:
    youtube_api = YouTubeAPI()
    transcript_mgr = TranscriptManager()
    quiz_gen = QuizGenerator()

    LETTER_TO_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3}
    INDEX_TO_LETTER = {0: "A", 1: "B", 2: "C", 3: "D"}

    with gr.Blocks(title="YouTube Quiz Generator") as demo:
        # State variables
        stored_videos = gr.State([])
        current_video = gr.State(None)

        # Header
        gr.HTML(
            """
            <div class="main-header">
                <h1>YouTube Community Quiz Generator</h1>
                <p>Generate educational multiple-choice quiz posts from your latest YouTube videos with full manual review and instant copy.</p>
            </div>
            """
        )

        with gr.Row():
            # Left column: Video Selection & Controls
            with gr.Column(scale=5):
                with gr.Group():
                    gr.Markdown("### 1. Select YouTube Video")
                    channel_input = gr.Textbox(
                        label="YouTube Channel Handle or ID",
                        value=settings.YOUTUBE_CHANNEL_ID or "@mkbhd",
                        placeholder="@MyChannel, UCxxxxxxxxxxxx, or channel link",
                        info="Used to retrieve your channel's latest uploads via YouTube Data API.",
                    )
                    fetch_btn = gr.Button("Fetch Latest 10 Videos", variant="secondary", elem_classes=["btn-secondary-action"])

                    video_dropdown = gr.Dropdown(
                        label="Latest 10 Videos (Randomly selected on fetch)",
                        choices=[],
                        value=None,
                        interactive=True,
                    )

                    video_details_md = gr.Markdown(
                        value=format_video_markdown(None),
                        elem_classes=["video-card"],
                    )

                with gr.Group():
                    gr.Markdown("### 2. Generate Quiz with AI")
                    generate_btn = gr.Button(
                        "Generate Quiz from Video Content",
                        variant="primary",
                        elem_classes=["btn-primary-action"],
                    )
                    gen_status_md = gr.Markdown(value="", visible=True)

            # Right column: Quiz Review, Validation & Export
            with gr.Column(scale=6):
                with gr.Group():
                    gr.Markdown("### 3. Review & Edit Quiz")
                    gr.Markdown("<small style='color: #9ca3af;'>Ensure the question is engaging, options are under 80 characters, and the explanation is concise.</small>")

                    question_tb = gr.Textbox(
                        label="Question",
                        placeholder="What is the primary concept discussed in this video?",
                        lines=2,
                    )

                    with gr.Row():
                        opt_a = gr.Textbox(label="Option A (max 80 chars)", max_lines=1)
                        opt_b = gr.Textbox(label="Option B (max 80 chars)", max_lines=1)

                    with gr.Row():
                        opt_c = gr.Textbox(label="Option C (max 80 chars)", max_lines=1)
                        opt_d = gr.Textbox(label="Option D (max 80 chars)", max_lines=1)

                    with gr.Row():
                        correct_answer_dd = gr.Dropdown(
                            label="Correct Answer",
                            choices=["A", "B", "C", "D"],
                            value="A",
                            scale=1,
                        )
                        explanation_tb = gr.Textbox(
                            label="Explanation",
                            placeholder="Why is this answer correct?",
                            lines=2,
                            scale=3,
                        )


        # -------------------------------------------------------------
        # Helper Functions & Event Handlers
        # -------------------------------------------------------------

        def on_fetch_videos(channel_text: str):
            """Retrieves the latest 10 videos, randomly picks one, and updates UI."""
            if not channel_text or not channel_text.strip():
                return (
                    [],
                    None,
                    gr.update(choices=[], value=None),
                    format_video_markdown(None),
                    "⚠️ Please provide a YouTube channel handle or ID.",
                )

            try:
                videos = youtube_api.get_latest_videos(channel_text.strip(), count=10)
                if not videos:
                    return (
                        [],
                        None,
                        gr.update(choices=[], value=None),
                        format_video_markdown(None),
                        "⚠️ No videos found for this channel.",
                    )

                video_dicts = [v.model_dump() for v in videos]
                choices = [f"{v.title} [{v.id}]" for v in videos]

                # Randomly select one video
                chosen = select_random_video(videos)
                chosen_dict = chosen.model_dump() if chosen else video_dicts[0]
                chosen_choice = f"{chosen_dict['title']} [{chosen_dict['id']}]"

                logger.info(f"Randomly selected video: '{chosen_dict['title']}' ({chosen_dict['id']})")

                return (
                    video_dicts,
                    chosen_dict,
                    gr.update(choices=choices, value=chosen_choice),
                    format_video_markdown(chosen_dict),
                    f"✓ Fetched {len(videos)} videos. Randomly selected: **{chosen_dict['title']}**",
                )

            except Exception as e:
                err_msg = f"✗ YouTube API request failed: {e}"
                logger.error(err_msg)
                return (
                    [],
                    None,
                    gr.update(choices=[], value=None),
                    format_video_markdown(None),
                    f"<span style='color: #ef4444;'>{err_msg}</span>",
                )

        def on_video_selected(selected_choice: str, videos_list: list):
            """When user manually selects another video from the dropdown."""
            if not selected_choice or not videos_list:
                return None, format_video_markdown(None)

            for v_data in videos_list:
                if f"[{v_data['id']}]" in selected_choice:
                    logger.info(f"User manually selected video: '{v_data['title']}' ({v_data['id']})")
                    return v_data, format_video_markdown(v_data)

            return None, format_video_markdown(None)

        def on_generate_quiz(video_data: dict | None):
            """Retrieves transcript and generates quiz via OpenRouter."""
            if not video_data or not video_data.get("id"):
                return (
                    "", "", "", "", "", "A", "",
                    "<span style='color: #ef4444;'>⚠️ Please select a video first.</span>",
                )

            vid = video_data["id"]
            title = video_data.get("title", "")
            video_url = video_data.get("url") or f"https://www.youtube.com/watch?v={vid}"

            # 1. Retrieve transcript
            try:
                transcript_text = transcript_mgr.fetch_transcript(vid)
            except Exception as e:
                err_msg = f"✗ Could not retrieve transcript: {e}"
                logger.error(err_msg)
                return (
                    "", "", "", "", "", "A", "",
                    f"<span style='color: #ef4444;'>{err_msg}</span>",
                )

            # 2. Call LLM Provider via OpenRouter
            try:
                quiz = quiz_gen.generate(title, transcript_text, video_url=video_url)
                letter = INDEX_TO_LETTER.get(quiz.correct_answer, "A")

                return (
                    quiz.question,
                    quiz.options[0],
                    quiz.options[1],
                    quiz.options[2],
                    quiz.options[3],
                    letter,
                    quiz.explanation,
                    f"✓ Quiz generated successfully from transcript! (Model: {settings.OPENROUTER_MODEL})",
                )

            except Exception as e:
                err_msg = f"✗ OpenRouter request failed: {e}"
                logger.error(err_msg)
                return (
                    "", "", "", "", "", "A", "",
                    f"<span style='color: #ef4444;'>{err_msg}</span>",
                )

        # -------------------------------------------------------------
        # Connect Event Handlers
        # -------------------------------------------------------------

        # Fetch button
        fetch_btn.click(
            fn=on_fetch_videos,
            inputs=[channel_input],
            outputs=[stored_videos, current_video, video_dropdown, video_details_md, gen_status_md],
        )

        # Video dropdown change
        video_dropdown.change(
            fn=on_video_selected,
            inputs=[video_dropdown, stored_videos],
            outputs=[current_video, video_details_md],
        )

        # Generate Quiz button
        generate_btn.click(
            fn=on_generate_quiz,
            inputs=[current_video],
            outputs=[
                question_tb,
                opt_a,
                opt_b,
                opt_c,
                opt_d,
                correct_answer_dd,
                explanation_tb,
                gen_status_md,
            ],
        )

    return demo
