import pytest
from app.quiz.models import Quiz
from app.quiz.generator import (
    format_question_with_video_link,
    shuffle_quiz_options,
    sanitize_explanation,
    QuizGenerator,
)
from app.quiz.providers.openrouter import LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock provider that always returns Option B as the correct answer."""
    def generate_quiz(self, video_title: str, transcript_text: str) -> Quiz:
        return Quiz(
            question="What is the capital of France?",
            options=["Berlin", "Paris", "Madrid", "Rome"],
            correct_answer=1,  # Option B (Paris)
            explanation="Option B is correct because Paris is the capital of France.",
        )


def test_format_question_with_video_link_standard():
    q = "What is the capital of France?"
    url = "https://www.youtube.com/watch?v=abc123xyz"
    formatted = format_question_with_video_link(q, url)
    assert formatted == "What is the capital of France? https://www.youtube.com/watch?v=abc123xyz"


def test_format_question_with_video_link_with_trailing_text():
    q = "What is the capital of France? Let us know below."
    url = "https://www.youtube.com/watch?v=abc123xyz"
    formatted = format_question_with_video_link(q, url)
    assert formatted == "What is the capital of France? https://www.youtube.com/watch?v=abc123xyz Let us know below."


def test_format_question_with_video_link_no_question_mark():
    q = "Identify the capital of France"
    url = "https://www.youtube.com/watch?v=abc123xyz"
    formatted = format_question_with_video_link(q, url)
    assert formatted == "Identify the capital of France? https://www.youtube.com/watch?v=abc123xyz"


def test_format_question_with_video_link_already_present():
    q = "What is the capital of France? https://www.youtube.com/watch?v=abc123xyz"
    url = "https://www.youtube.com/watch?v=abc123xyz"
    formatted = format_question_with_video_link(q, url)
    assert formatted == "What is the capital of France? https://www.youtube.com/watch?v=abc123xyz"


def test_format_question_with_empty_url():
    q = "What is the capital of France?"
    formatted = format_question_with_video_link(q, "")
    assert formatted == "What is the capital of France?"


def test_shuffle_quiz_options_preserves_correct_answer():
    quiz = Quiz(
        question="What is the capital of France?",
        options=["Berlin", "Paris", "Madrid", "Rome"],
        correct_answer=1,  # Paris
        explanation="Paris is the capital of France.",
    )

    shuffled = shuffle_quiz_options(quiz)
    assert len(shuffled.options) == 4
    assert set(shuffled.options) == {"Berlin", "Paris", "Madrid", "Rome"}
    assert shuffled.options[shuffled.correct_answer] == "Paris"


def test_shuffle_quiz_options_eliminates_option_b_bias():
    quiz = Quiz(
        question="What is the capital of France?",
        options=["Berlin", "Paris", "Madrid", "Rome"],
        correct_answer=1,  # Paris is originally Option B
        explanation="Paris is the capital.",
    )

    seen_indices = set()
    counts = {0: 0, 1: 0, 2: 0, 3: 0}

    # Run 100 shuffles
    for _ in range(100):
        shuffled = shuffle_quiz_options(quiz)
        counts[shuffled.correct_answer] += 1
        seen_indices.add(shuffled.correct_answer)
        assert shuffled.options[shuffled.correct_answer] == "Paris"

    # All 4 positions (0, 1, 2, 3) must be observed across 100 runs
    assert len(seen_indices) == 4
    # Option B (index 1) must NOT be 100% of the results
    assert counts[1] < 100
    for idx in range(4):
        assert counts[idx] > 5  # Each position should roughly get ~25%


def test_sanitize_explanation():
    exp = "Option B is correct because Paris is the capital."
    updated = sanitize_explanation(exp, old_index=1, new_index=3)
    assert "Option D" in updated
    assert "Option B" not in updated


def test_generator_attaches_video_link_and_shuffles():
    provider = MockLLMProvider()
    generator = QuizGenerator(provider=provider)

    video_url = "https://www.youtube.com/watch?v=sample123"
    quiz = generator.generate("Title", "Transcript", video_url=video_url)

    assert video_url in quiz.question
    assert quiz.question.startswith("What is the capital of France?")
    assert quiz.options[quiz.correct_answer] == "Paris"
