import os
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright, BrowserContext, Page, Playwright
from app.config.settings import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class BrowserManager:
    """Manages persistent Playwright browser contexts for YouTube automation."""

    def __init__(self, profile_dir: Path | None = None, headless: bool | None = None):
        self.profile_dir = profile_dir or settings.BROWSER_PROFILE_DIR
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.headless = settings.PLAYWRIGHT_HEADLESS if headless is None else headless
        self._playwright: Optional[Playwright] = None
        self._context: Optional[BrowserContext] = None

    def launch(self) -> tuple[BrowserContext, Page]:
        """
        Launches or attaches to the persistent Chromium context.
        Returns (context, page).
        """
        if self._playwright is None:
            self._playwright = sync_playwright().start()

        logger.info(
            f"Launching Chromium with profile '{self.profile_dir}' (headless={self.headless})"
        )

        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-default-browser-check",
            "--disable-infobars",
            "--start-maximized",
        ]

        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.profile_dir),
            headless=self.headless,
            args=args,
            viewport=None,  # Use full window size
            accept_downloads=True,
        )

        # Get existing page or create a new one
        if self._context.pages:
            page = self._context.pages[0]
        else:
            page = self._context.new_page()

        return self._context, page

    def close(self):
        """Closes the browser context and stops Playwright."""
        if self._context:
            try:
                self._context.close()
            except Exception as e:
                logger.warning(f"Error closing browser context: {e}")
            self._context = None

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception as e:
                logger.warning(f"Error stopping Playwright: {e}")
            self._playwright = None
        logger.info("Browser session closed.")
