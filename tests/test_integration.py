import os
import pytest
from app.config.settings import settings
from app.youtube.api import YouTubeAPI
from app.quiz.providers.openrouter import OpenRouterProvider
from app.quiz.generator import QuizGenerator


@pytest.mark.skipif(not settings.YOUTUBE_API_KEY, reason="YouTube API key not configured")
def test_youtube_api_live_channel_and_videos():
    api = YouTubeAPI()
    # Test with Google channel handle
    channel_info = api.get_channel_details("@Google")
    assert channel_info["channel_id"].startswith("UC")
    assert "uploads_playlist_id" in channel_info

    videos = api.get_latest_videos("@Google", count=2)
    assert len(videos) > 0
    assert videos[0].id
    assert videos[0].title
    assert videos[0].url.startswith("https://www.youtube.com/watch?v=")


@pytest.mark.skipif(not settings.OPENROUTER_API_KEY, reason="OpenRouter API key not configured")
def test_openrouter_quiz_generation():
    provider = OpenRouterProvider(model="google/gemini-2.5-flash")
    generator = QuizGenerator(provider=provider)

    sample_title = "Introduction to Python List Comprehensions"
    sample_transcript = (
        "In this video we are discussing Python list comprehensions. "
        "A list comprehension offers a shorter syntax when you want to create a new list "
        "based on the values of an existing list. For example, instead of writing a for loop "
        "with append, you write expression for item in iterable if condition. It provides a more "
        "concise and readable way to transform collections."
    )

    quiz = generator.generate(sample_title, sample_transcript)
    assert quiz.question
    assert len(quiz.options) == 4
    assert 0 <= quiz.correct_answer <= 3
    assert quiz.explanation
    for opt in quiz.options:
        assert len(opt) <= 80
