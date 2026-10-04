import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.ui.gradio_app import create_app
from app.main import main

# Expose 'demo' for Gradio hosting platforms like Hugging Face Spaces
demo = create_app()

if __name__ == "__main__":
    main()
