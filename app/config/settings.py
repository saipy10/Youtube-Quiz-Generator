import os
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

# Load .env file with override=True so project-specific keys take precedence over system env
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(env_path, override=True)
_file_values = dotenv_values(env_path) if env_path.exists() else {}

# Directories
DATA_DIR = BASE_DIR / "data"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _get_conf(key: str, fallback_key: str = "", default: str = "") -> str:
    """Gets configuration value prioritizing .env file then os.environ."""
    val = _file_values.get(key) or _file_values.get(fallback_key) or os.getenv(key) or os.getenv(fallback_key) or default
    return str(val).strip()


class Settings:
    # OpenRouter API settings
    OPENROUTER_API_KEY: str = _get_conf("OPENROUTER_API_KEY", "OPENROUTER_API")
    OPENROUTER_MODEL: str = _get_conf("OPENROUTER_MODEL", default="google/gemini-2.5-flash")
    OPENROUTER_BASE_URL: str = _get_conf("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")

    # YouTube Data API settings
    YOUTUBE_API_KEY: str = _get_conf("YOUTUBE_API_KEY", "YOUTUBE_API")
    YOUTUBE_CHANNEL_ID: str = _get_conf("YOUTUBE_CHANNEL_ID")

    # Gradio UI settings
    GRADIO_SERVER_NAME: str = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1").strip()
    GRADIO_SERVER_PORT: int = int(os.getenv("GRADIO_SERVER_PORT", "7860"))

    TRANSCRIPTS_DIR: Path = TRANSCRIPTS_DIR
    LOGS_DIR: Path = LOGS_DIR
    DATA_DIR: Path = DATA_DIR
    BASE_DIR: Path = BASE_DIR


settings = Settings()
