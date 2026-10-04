import sys
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import gradio as gr
from app.config.settings import settings
from app.ui.gradio_app import create_app
from app.ui.components import CUSTOM_CSS
from app.utils.logger import setup_logger

logger = setup_logger("main")


def main():
    logger.info("Starting YouTube Community Quiz Automation application...")
    logger.info(f"OpenRouter Model: {settings.OPENROUTER_MODEL}")

    app = create_app()
    logger.info(f"Launching Gradio server on http://{settings.GRADIO_SERVER_NAME}:{settings.GRADIO_SERVER_PORT}")
    app.launch(
        server_name=settings.GRADIO_SERVER_NAME,
        server_port=settings.GRADIO_SERVER_PORT,
        share=False,
        inbrowser=False,
        theme=gr.themes.Default(primary_hue="red"),
        css=CUSTOM_CSS,
    )


if __name__ == "__main__":
    main()
