from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    YouTubeRequestFailed,
)
from app.config.settings import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class TranscriptManager:
    """Manages fetching and local file caching of YouTube video transcripts."""

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or settings.TRANSCRIPTS_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.api = YouTubeTranscriptApi()

    def get_cache_path(self, video_id: str) -> Path:
        """Returns the local cache file path for a given video ID."""
        return self.cache_dir / f"{video_id}.txt"

    def is_cached(self, video_id: str) -> bool:
        """Checks if a transcript is already cached locally."""
        path = self.get_cache_path(video_id)
        return path.exists() and path.stat().st_size > 0

    def read_cached(self, video_id: str) -> str:
        """Reads transcript text from the local cache."""
        path = self.get_cache_path(video_id)
        logger.info(f"Loading cached transcript for video '{video_id}' from {path}")
        return path.read_text(encoding="utf-8")

    def save_cache(self, video_id: str, text: str) -> None:
        """Saves transcript text to the local cache."""
        path = self.get_cache_path(video_id)
        path.write_text(text, encoding="utf-8")
        logger.info(f"Saved transcript for video '{video_id}' to cache: {path}")

    def fetch_transcript(self, video_id: str, force_refresh: bool = False) -> str:
        """
        Retrieves the transcript for a video, checking local cache first.
        If not cached, fetches from YouTube and saves to cache.
        """
        if not force_refresh and self.is_cached(video_id):
            return self.read_cached(video_id)

        logger.info(f"Fetching transcript from YouTube for video '{video_id}'...")

        try:
            # 1. Attempt direct fetch with preferred English variants
            try:
                fetched = self.api.fetch(video_id, languages=["en", "en-US", "en-GB"])
                text = " ".join([snippet.text for snippet in fetched if snippet.text])
            except Exception:
                # 2. Fallback to list() to find any manual, generated, or translatable transcript
                transcript_list = self.api.list(video_id)
                transcript = None
                try:
                    transcript = transcript_list.find_transcript(["en", "en-US", "en-GB"])
                except Exception:
                    # Find any transcript and translate to english if possible
                    for t in transcript_list:
                        if t.is_translatable:
                            transcript = t.translate("en")
                            break
                        elif transcript is None:
                            transcript = t

                if transcript is None:
                    raise RuntimeError(f"No transcripts found for video {video_id}")

                snippets = transcript.fetch()
                text = " ".join([s.text for s in snippets if s.text])

            text = text.strip()
            if not text:
                raise RuntimeError(f"Transcript retrieved for video '{video_id}' was empty.")

            self.save_cache(video_id, text)
            return text

        except TranscriptsDisabled:
            msg = f"Transcripts are disabled for video '{video_id}'."
            logger.error(msg)
            raise RuntimeError(msg)
        except NoTranscriptFound:
            msg = f"No transcript found for video '{video_id}'."
            logger.error(msg)
            raise RuntimeError(msg)
        except VideoUnavailable:
            msg = f"Video '{video_id}' is unavailable."
            logger.error(msg)
            raise RuntimeError(msg)
        except YouTubeRequestFailed as e:
            msg = f"YouTube request failed while retrieving transcript: {e}"
            logger.error(msg)
            raise RuntimeError(msg)
        except Exception as e:
            msg = f"Could not retrieve transcript for video '{video_id}': {e}"
            logger.error(msg)
            raise RuntimeError(msg)
