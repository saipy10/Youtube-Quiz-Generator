from typing import List
from pydantic import BaseModel, Field, field_validator, model_validator


class Quiz(BaseModel):
    """
    Pydantic model representing a YouTube Community Quiz.
    """
    question: str = Field(..., description="The quiz question text.")
    options: List[str] = Field(..., min_length=4, max_length=4, description="List of exactly 4 answer options.")
    correct_answer: int = Field(..., ge=0, le=3, description="0-indexed position of the correct answer (0, 1, 2, or 3).")
    explanation: str = Field(..., description="Explanation of why the correct answer is correct.")

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty.")
        if len(v) > 500:
            raise ValueError(f"Question is too long ({len(v)} chars, max 500 chars).")
        return v

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: List[str]) -> List[str]:
        if len(v) != 4:
            raise ValueError(f"Exactly 4 options are required, got {len(v)}.")
        cleaned = [opt.strip() for opt in v]
        for i, opt in enumerate(cleaned):
            if not opt:
                label = chr(ord('A') + i)
                raise ValueError(f"Option {label} cannot be empty.")
            if len(opt) > 80:
                label = chr(ord('A') + i)
                raise ValueError(f"Option {label} exceeds YouTube limit of 80 characters ({len(opt)} chars).")
        
        # Check for duplicates (case-insensitive)
        lowered = [opt.lower() for opt in cleaned]
        if len(set(lowered)) != len(lowered):
            raise ValueError("Options must be unique. Duplicate options found.")
        return cleaned

    @field_validator("explanation")
    @classmethod
    def validate_explanation(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Explanation cannot be empty.")
        if len(v) > 350:
            raise ValueError(f"Explanation is too long ({len(v)} chars, YouTube max is ~350 chars).")
        return v

    @model_validator(mode="after")
    def validate_correct_answer_index(self) -> "Quiz":
        if self.correct_answer < 0 or self.correct_answer >= len(self.options):
            raise ValueError(f"Correct answer index {self.correct_answer} is out of bounds (must be 0 to 3).")
        return self
