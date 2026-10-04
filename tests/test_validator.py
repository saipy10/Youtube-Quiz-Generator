from app.quiz.validator import validate_quiz_inputs


def test_validator_success():
    res = validate_quiz_inputs(
        question="What does temperature control in LLMs?",
        options=[
            "Randomness of token selection",
            "Hardware operating temperature",
            "Network latency to server",
            "Context window size",
        ],
        correct_answer=0,
        explanation="Temperature adjusts the probability distribution of generated tokens.",
    )
    assert res.is_valid is True
    assert len(res.errors) == 0
    assert "✓ Quiz is Valid" in res.format_display()


def test_validator_catches_empty_option():
    res = validate_quiz_inputs(
        question="What does temperature control in LLMs?",
        options=[
            "Randomness of token selection",
            "",
            "Network latency to server",
            "Context window size",
        ],
        correct_answer=0,
        explanation="Temperature adjusts the probability distribution.",
    )
    assert res.is_valid is False
    assert any("Option B is empty" in err for err in res.errors)


def test_validator_catches_duplicate_options():
    res = validate_quiz_inputs(
        question="What does temperature control in LLMs?",
        options=[
            "Option 1",
            "Option 1",
            "Option 3",
            "Option 4",
        ],
        correct_answer=0,
        explanation="Explanation here",
    )
    assert res.is_valid is False
    assert any("unique" in err.lower() for err in res.errors)
