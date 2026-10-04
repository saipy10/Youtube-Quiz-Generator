from typing import List, Optional, Tuple
from pydantic import ValidationError
from app.quiz.models import Quiz


class ValidationResult:
    def __init__(self, is_valid: bool, checks: List[str], errors: List[str], quiz: Optional[Quiz] = None):
        self.is_valid = is_valid
        self.checks = checks
        self.errors = errors
        self.quiz = quiz

    def format_display(self) -> str:
        """Formats the validation result into a clean markdown checklist."""
        lines = []
        if self.is_valid:
            lines.append("### ✓ Quiz is Valid & Ready for Verification\n")
            for check in self.checks:
                lines.append(f"- ✓ {check}")
        else:
            lines.append("### ✗ Quiz Validation Failed\n")
            for err in self.errors:
                lines.append(f"- ✗ {err}")
            if self.checks:
                lines.append("\n**Passed checks:**")
                for check in self.checks:
                    lines.append(f"- ✓ {check}")
        return "\n".join(lines)


def validate_quiz_inputs(
    question: str,
    options: List[str],
    correct_answer: int | str,
    explanation: str,
) -> ValidationResult:
    """
    Validates quiz inputs and returns a detailed ValidationResult.
    """
    checks: List[str] = []
    errors: List[str] = []

    # Question validation
    q_clean = question.strip() if question else ""
    if not q_clean:
        errors.append("Question cannot be empty.")
    elif len(q_clean) > 500:
        errors.append(f"Question exceeds maximum length of 500 characters ({len(q_clean)} chars).")
    else:
        checks.append("Question is valid")
        if "youtube.com" in q_clean or "youtu.be" in q_clean:
            checks.append("Question includes video link after question mark")

    # Options validation
    labels = ["A", "B", "C", "D"]
    if len(options) != 4:
        errors.append(f"Expected exactly 4 options, found {len(options)}.")
    else:
        empty_opts = []
        long_opts = []
        cleaned_opts = []
        for i, opt in enumerate(options):
            cleaned = opt.strip() if opt else ""
            cleaned_opts.append(cleaned)
            if not cleaned:
                empty_opts.append(labels[i])
            elif len(cleaned) > 80:
                long_opts.append(f"Option {labels[i]} ({len(cleaned)} chars, max 80)")

        if empty_opts:
            for lbl in empty_opts:
                errors.append(f"Option {lbl} is empty.")
        if long_opts:
            for msg in long_opts:
                errors.append(f"{msg} exceeds YouTube 80-character limit.")

        if not empty_opts:
            # Check duplicates
            lowered = [o.lower() for o in cleaned_opts]
            if len(set(lowered)) != len(lowered):
                errors.append("Options must be unique. Duplicate options found.")
            elif not long_opts:
                checks.append("Four unique, valid options (<= 80 chars each)")

    # Correct answer validation
    try:
        if isinstance(correct_answer, str):
            ans_idx = int(correct_answer)
        else:
            ans_idx = int(correct_answer)
        if 0 <= ans_idx < 4:
            checks.append(f"Correct answer selected (Option {labels[ans_idx]})")
        else:
            errors.append(f"Correct answer index {ans_idx} is out of bounds (must be 0, 1, 2, or 3).")
    except (ValueError, TypeError):
        errors.append("Correct answer has not been selected or is invalid.")
        ans_idx = -1

    # Explanation validation
    exp_clean = explanation.strip() if explanation else ""
    if not exp_clean:
        errors.append("Explanation cannot be empty.")
    elif len(exp_clean) > 350:
        errors.append(f"Explanation exceeds limit of 350 characters ({len(exp_clean)} chars).")
    else:
        checks.append("Explanation present and concise")

    quiz_obj: Optional[Quiz] = None
    if not errors and len(cleaned_opts) == 4 and 0 <= ans_idx < 4:
        try:
            quiz_obj = Quiz(
                question=q_clean,
                options=cleaned_opts,
                correct_answer=ans_idx,
                explanation=exp_clean,
            )
        except ValidationError as e:
            for err in e.errors():
                errors.append(err["msg"])

    is_valid = len(errors) == 0 and quiz_obj is not None
    return ValidationResult(is_valid=is_valid, checks=checks, errors=errors, quiz=quiz_obj)
