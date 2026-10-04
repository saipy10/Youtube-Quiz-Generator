import random
import re
from typing import Optional
from app.quiz.models import Quiz
from app.quiz.providers.openrouter import LLMProvider, OpenRouterProvider
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def format_question_with_video_link(question: str, video_url: str) -> str:
    """
    Appends the video link after the question mark.
    If there is text after the question mark, inserts the link immediately after the question mark.
    If no question mark exists, appends '?' followed by the video link.
    If the video link is already in the question, returns the question unchanged.
    """
    q = (question or "").strip()
    url = (video_url or "").strip()
    if not url or url in q:
        return q

    qmark_idx = q.rfind("?")
    if qmark_idx != -1:
        before = q[: qmark_idx + 1].strip()
        after = q[qmark_idx + 1 :].strip()
        if after:
            return f"{before} {url} {after}".strip()
        else:
            return f"{before} {url}".strip()
    else:
        return f"{q}? {url}".strip()


def sanitize_explanation(explanation: str, old_index: int, new_index: int) -> str:
    """
    Updates hardcoded option letters in the explanation if the LLM referenced option letters.
    """
    if old_index == new_index or not explanation:
        return explanation

    old_letter = chr(ord("A") + old_index)
    new_letter = chr(ord("A") + new_index)

    # Replace "Option B" -> "Option {new_letter}"
    pattern = rf"\bOption\s+{old_letter}\b"
    updated = re.sub(pattern, f"Option {new_letter}", explanation, flags=re.IGNORECASE)

    # Replace "Choice B" -> "Choice {new_letter}"
    pattern_choice = rf"\bChoice\s+{old_letter}\b"
    updated = re.sub(pattern_choice, f"Choice {new_letter}", updated, flags=re.IGNORECASE)

    return updated


def shuffle_quiz_options(quiz: Quiz) -> Quiz:
    """
    Randomly shuffles the options of a quiz and updates the correct_answer index accordingly.
    Eliminates LLM positional bias (e.g. Option B always being right).
    """
    if len(quiz.options) != 4 or not (0 <= quiz.correct_answer < 4):
        return quiz

    paired = [(opt, i == quiz.correct_answer) for i, opt in enumerate(quiz.options)]
    random.shuffle(paired)

    shuffled_options = [opt for opt, _ in paired]
    new_correct_index = next(i for i, (_, is_corr) in enumerate(paired) if is_corr)

    cleaned_explanation = sanitize_explanation(
        quiz.explanation,
        old_index=quiz.correct_answer,
        new_index=new_correct_index,
    )

    return Quiz(
        question=quiz.question,
        options=shuffled_options,
        correct_answer=new_correct_index,
        explanation=cleaned_explanation,
    )


class QuizGenerator:
    """Orchestrates quiz generation using a configured LLM provider."""

    def __init__(self, provider: LLMProvider | None = None):
        self.provider = provider or OpenRouterProvider()

    def generate(
        self,
        video_title: str,
        transcript_text: str,
        video_url: Optional[str] = None,
    ) -> Quiz:
        """
        Generates and validates a single quiz from a video transcript.
        Automatically shuffles options to eliminate option B bias,
        and appends the video link after the question mark if provided.
        """
        logger.info(f"Starting quiz generation for video: '{video_title}' (Transcript length: {len(transcript_text)} chars)")
        raw_quiz = self.provider.generate_quiz(video_title, transcript_text)

        # 1. Shuffle options to remove positional bias (e.g. Option B always right)
        quiz = shuffle_quiz_options(raw_quiz)

        # 2. Append video link after question mark if video_url is provided
        if video_url:
            updated_question = format_question_with_video_link(quiz.question, video_url)
            quiz = Quiz(
                question=updated_question,
                options=quiz.options,
                correct_answer=quiz.correct_answer,
                explanation=quiz.explanation,
            )

        correct_letter = chr(ord("A") + quiz.correct_answer)
        logger.info(f"Quiz generated successfully. Question: '{quiz.question[:60]}...', Correct Option: {correct_letter}")
        return quiz
