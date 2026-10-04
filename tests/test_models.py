import pytest
from pydantic import ValidationError
from app.quiz.models import Quiz


def test_valid_quiz():
    quiz = Quiz(
        question="What is Retrieval-Augmented Generation (RAG)?",
        options=[
            "Context injection from retrieved data",
            "Fine-tuning model weights directly",
            "Modifying tokenizer vocabulary",
            "Quantizing model weights to 4-bit",
        ],
        correct_answer=0,
        explanation="RAG injects relevant retrieved context into the model's prompt.",
    )
    assert quiz.question.startswith("What is")
    assert len(quiz.options) == 4
    assert quiz.correct_answer == 0


def test_empty_question_fails():
    with pytest.raises(ValidationError):
        Quiz(
            question="",
            options=["A", "B", "C", "D"],
            correct_answer=0,
            explanation="Valid explanation",
        )


def test_invalid_options_count_fails():
    with pytest.raises(ValidationError):
        Quiz(
            question="What is AI?",
            options=["A", "B", "C"],  # Only 3 options
            correct_answer=0,
            explanation="Valid explanation",
        )


def test_option_too_long_fails():
    # Max option length is 80 characters (YouTube limit)
    with pytest.raises(ValidationError) as exc_info:
        Quiz(
            question="What is AI?",
            options=[
                "Short option A",
                "Short option B",
                "Short option C",
                "A" * 81,  # 81 characters
            ],
            correct_answer=0,
            explanation="Valid explanation",
        )
    assert "80 characters" in str(exc_info.value)


def test_duplicate_options_fails():
    with pytest.raises(ValidationError) as exc_info:
        Quiz(
            question="What is AI?",
            options=[
                "Duplicate Option",
                "Duplicate Option",
                "Unique C",
                "Unique D",
            ],
            correct_answer=0,
            explanation="Valid explanation",
        )
    assert "Options must be unique" in str(exc_info.value)


def test_correct_answer_out_of_bounds_fails():
    with pytest.raises(ValidationError):
        Quiz(
            question="What is AI?",
            options=["A", "B", "C", "D"],
            correct_answer=4,  # Out of bounds
            explanation="Valid explanation",
        )
