import time
from pathlib import Path
from typing import Optional, List
from playwright.sync_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError

from app.config.settings import settings
from app.quiz.models import Quiz
from app.youtube.browser import BrowserManager
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class YouTubePostPublisher:
    """
    Automates the creation and publication of YouTube Community Quiz posts using Playwright.
    All YouTube UI selectors and navigation logic are strictly contained in this class.
    """

    # Primary and fallback selectors
    SELECTORS = {
        "avatar_btn": [
            "button#avatar-btn",
            "ytd-topbar-menu-button-renderer#avatar-btn",
            "img#avatar-btn",
        ],
        "sign_in_btn": [
            "a[href*='accounts.google.com/ServiceLogin']",
            "ytd-button-renderer:has-text('Sign in')",
            "button:has-text('Sign in')",
        ],
        "create_btn": [
            "button[aria-label='Create']",
            "yt-icon-button#create-icon",
            "ytd-topbar-menu-button-renderer:has(button[aria-label*='Create'])",
            "button:has-text('Create')",
        ],
        "create_post_item": [
            "tp-yt-paper-item:has-text('Create post')",
            "yt-formatted-string:has-text('Create post')",
            "a[href*='/post/create']",
            "a:has-text('Create post')",
        ],
        "composer_placeholder": [
            "div:has-text(\"What's on your mind?\")",
            "[aria-label*=\"What's on your mind\" i]",
            "#placeholder-area",
            "div#simplebox-placeholder",
            "#contenteditable-root",
            "div[contenteditable='true']",
            "ytd-backstage-post-creation-renderer",
            "tp-yt-paper-input#placeholder",
            "div[aria-label*='post' i]",
            "div:has-text('Post an update')",
            "div:has-text('Ask your community')",
        ],
        "quiz_tab_btn": [
            "button:has-text('Quiz')",
            "button[aria-label='Quiz']",
            "tp-yt-paper-button:has-text('Quiz')",
            "div[aria-label='Quiz']",
            "yt-formatted-string:has-text('Quiz')",
            "ytd-button-renderer:has-text('Quiz')",
        ],
        "question_input": [
            "ytd-backstage-post-creation-renderer div[contenteditable='true']",
            "ytd-post-creation-dialog-renderer div[contenteditable='true']",
            "#contenteditable-root",
            "div[contenteditable='true']#contenteditable-root",
            "div#textbox[contenteditable='true']",
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true']",
            "div[role='textbox']",
        ],
        "add_option_btn": [
            "button:has-text('Add answer')",
            "div:has-text('Add answer')",
            "button:has-text('+ Add answer')",
            "[aria-label*='Add answer' i]",
            "tp-yt-paper-button:has-text('Add answer')",
            "button:has-text('Add option')",
            "tp-yt-paper-button:has-text('Add option')",
            "div[aria-label='Add option']",
            "button[aria-label='Add option']",
            "ytd-button-renderer:has-text('Add answer')",
            "ytd-button-renderer:has-text('Add option')",
        ],
        "option_inputs": [
            "input[placeholder*='Answer' i]",
            "input[aria-label*='Answer' i]",
            "div[contenteditable='true'][aria-label*='Answer' i]",
            "div[contenteditable='true'][placeholder*='Answer' i]",
            "input[aria-label*='Option' i]",
            "div[contenteditable='true'][aria-label*='Option' i]",
            "input[placeholder*='Option' i]",
            "ytd-poll-choice-editor-renderer input",
            "div.choice-container input",
        ],
        "explanation_btn": [
            "button:has-text('Add an explanation')",
            "button:has-text('Add explanation')",
            "button:has-text('Explain why this is correct')",
            "div:has-text('Add explanation')",
            "button[aria-label*='explanation' i]",
        ],
        "explanation_input": [
            "input[placeholder*='Add an explanation' i]",
            "textarea[placeholder*='Add an explanation' i]",
            "input[placeholder*='explanation' i]",
            "textarea[placeholder*='explanation' i]",
            "input[aria-label*='explanation' i]",
            "textarea[aria-label*='explanation' i]",
            "div[contenteditable='true'][aria-label*='explanation' i]",
            "#explanation-input",
        ],
        "post_btn": [
            "button:has-text('Post')",
            "button#post-button",
            "ytd-button-renderer#post-button button",
            "tp-yt-paper-button#post-button",
            "button[aria-label='Post']",
            "yt-button-shape:has-text('Post') button",
        ],
    }

    def __init__(
        self,
        browser_manager: Optional[BrowserManager] = None,
        headless: Optional[bool] = None,
        channel_id: Optional[str] = None,
    ):
        self.browser_manager = browser_manager or BrowserManager(headless=headless)
        self.channel_id = channel_id or settings.YOUTUBE_CHANNEL_ID
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.screenshots_dir = settings.LOGS_DIR / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    def get_posts_url(self, channel_id: Optional[str] = None) -> str:
        """Constructs the canonical channel community/posts URL."""
        cid = (channel_id or self.channel_id or "").strip()
        if not cid:
            return "https://www.youtube.com"

        # If user entered full URL, ensure it ends with /posts
        if "youtube.com" in cid:
            if not cid.endswith("/posts"):
                cid = cid.rstrip("/") + "/posts"
            return cid

        if cid.startswith("UC"):
            return f"https://www.youtube.com/channel/{cid}/posts"
        elif cid.startswith("@"):
            return f"https://www.youtube.com/{cid}/posts"
        else:
            return f"https://www.youtube.com/channel/{cid}/posts"

    def _save_screenshot(self, name: str):
        """Saves a debug screenshot."""
        if self.page:
            try:
                path = self.screenshots_dir / f"{name}_{int(time.time())}.png"
                self.page.screenshot(path=str(path))
                logger.info(f"Saved debug screenshot to {path}")
            except Exception as e:
                logger.warning(f"Failed to capture screenshot: {e}")

    def _find_element(self, selector_key: str, timeout: float = 8000):
        """Tries a list of selectors for a given key until one is found."""
        selectors = self.SELECTORS.get(selector_key, [])
        for sel in selectors:
            try:
                elem = self.page.wait_for_selector(sel, state="visible", timeout=timeout)
                if elem:
                    return elem
            except PlaywrightTimeoutError:
                continue
        return None

    def open_youtube(self):
        """Launches browser and navigates to YouTube, checking authentication status."""
        logger.info("Opening YouTube...")
        self.context, self.page = self.browser_manager.launch()
        self.page.goto("https://www.youtube.com", wait_until="domcontentloaded")
        time.sleep(2)

        # Check authentication status
        sign_in = self._find_element("sign_in_btn", timeout=3000)
        avatar = self._find_element("avatar_btn", timeout=4000)

        if sign_in and not avatar:
            self._save_screenshot("login_required")
            raise PermissionError(
                "You are not logged in to YouTube. "
                "Please run 'uv run python scripts/login_youtube.py' in your terminal "
                "to authenticate your account first."
            )
        logger.info("YouTube loaded. User authentication confirmed.")

    def open_create_post(self, channel_id: Optional[str] = None):
        """Navigates to the Channel Posts page (e.g. https://www.youtube.com/channel/{channel_id}/posts)."""
        posts_url = self.get_posts_url(channel_id)
        logger.info(f"Navigating to Channel Posts page: {posts_url}")

        self.page.goto(posts_url, wait_until="domcontentloaded")
        time.sleep(3)

        # 1. Check if quiz button is already visible on the posts tab
        quiz_btn = self._find_element("quiz_tab_btn", timeout=3000)
        if quiz_btn:
            logger.info("Quiz button found on channel posts page.")
            return

        # 2. Check if composer placeholder needs to be clicked to expand post options
        composer_area = self._find_element("composer_placeholder", timeout=4000)
        if composer_area:
            logger.info("Found composer placeholder, clicking to expand creation options...")
            try:
                composer_area.click()
                time.sleep(1.5)
            except Exception as e:
                logger.debug(f"Click on placeholder encountered: {e}")

            quiz_btn = self._find_element("quiz_tab_btn", timeout=4000)
            if quiz_btn:
                logger.info("Quiz button revealed after clicking composer placeholder.")
                return

        # 3. Fallback: navigate via topbar Create (+) button if on channel page
        logger.info("Falling back to topbar 'Create' button...")
        create_btn = self._find_element("create_btn", timeout=4000)
        if create_btn:
            create_btn.click()
            time.sleep(1)
            create_post_item = self._find_element("create_post_item", timeout=4000)
            if create_post_item:
                create_post_item.click()
                time.sleep(2)

    def _is_quiz_unlocked(self) -> bool:
        """Checks if the quiz composer options (Answer 1, Answer 2, etc.) are visible in the DOM."""
        if self.page.query_selector("input[placeholder*='Answer' i]"):
            return True
        if self._find_element("add_option_btn", timeout=500):
            return True
        if self._find_element("explanation_input", timeout=500):
            return True
        return False

    def select_quiz(self):
        """Clicks the 'Quiz' post type tab in the community composer and waits for options to unlock."""
        # 1. If Quiz UI is already open and options are unlocked, proceed directly
        if self._is_quiz_unlocked():
            logger.info("Quiz options are already unlocked and visible.")
            return

        logger.info("Looking for 'Quiz' button to unlock quiz options...")
        # 2. Check if the composer needs to be focused first to reveal buttons
        quiz_btn = self._find_element("quiz_tab_btn", timeout=2000)
        if not quiz_btn:
            placeholder = self._find_element("composer_placeholder", timeout=3000)
            if placeholder:
                logger.info("Focusing composer placeholder ('What's on your mind?') to reveal post types...")
                try:
                    placeholder.click()
                    time.sleep(1)
                except Exception as e:
                    logger.debug(f"Click on placeholder: {e}")
                quiz_btn = self._find_element("quiz_tab_btn", timeout=3000)

        # 3. Locate Quiz button
        if not quiz_btn:
            try:
                quiz_loc = self.page.locator("text='Quiz'").first
                if quiz_loc.is_visible():
                    quiz_btn = quiz_loc
            except Exception:
                pass

        if not quiz_btn:
            # Fallback search for any element or button containing 'Quiz'
            quiz_btn = self.page.query_selector("button:has-text('Quiz'), tp-yt-paper-button:has-text('Quiz'), div:has-text('Quiz'), [aria-label*='Quiz' i]")

        if not quiz_btn:
            self._save_screenshot("quiz_btn_missing")
            raise RuntimeError("Could not locate the 'Quiz' button in the post composer.")

        logger.info("Clicking 'Quiz' button to unlock options...")
        quiz_btn.click()

        # 4. Explicitly wait for quiz options (Answer 1, Answer 2, etc.) to unlock
        logger.info("Waiting for quiz answer options to unlock...")
        unlocked = False
        for attempt in range(10):  # poll up to 10 seconds
            time.sleep(1)
            if self._is_quiz_unlocked():
                unlocked = True
                break

        if not unlocked:
            self._save_screenshot("quiz_options_unlock_failed")
            raise RuntimeError("Clicked 'Quiz', but quiz options ('Answer 1', 'Answer 2', etc.) failed to unlock.")

        logger.info("Quiz options have successfully unlocked! Proceeding with question and answer entry.")

    def enter_question(self, question_text: str):
        """Enters the question text into the question field, resilient to any placeholder text."""
        logger.info(f"Entering question: '{question_text[:50]}...'")
        question_elem = self._find_element("question_input", timeout=4000)

        # Fallback 1: Locate relative to the first Answer input in the DOM
        if not question_elem:
            answer1 = self.page.query_selector("input[placeholder*='Answer' i]")
            if answer1:
                try:
                    handle = answer1.evaluate_handle("""el => {
                        const composer = el.closest('ytd-backstage-post-creation-renderer, ytd-post-creation-dialog-renderer, ytd-backstage-post-dialog-renderer')
                            || el.parentElement.parentElement.parentElement.parentElement;
                        return composer ? composer.querySelector("div[contenteditable='true'], #contenteditable-root, div#textbox, textarea") : null;
                    }""")
                    elem = handle.as_element()
                    if elem:
                        question_elem = elem
                        logger.info("Located question element relative to Answer 1 container.")
                except Exception as e:
                    logger.debug(f"Relative question search error: {e}")

        # Fallback 2: Any visible contenteditable on the page
        if not question_elem:
            all_ce = self.page.query_selector_all("div[contenteditable='true']")
            for ce in all_ce:
                if ce.is_visible():
                    question_elem = ce
                    logger.info("Located question element via visible contenteditable search.")
                    break

        if not question_elem:
            self._save_screenshot("question_input_missing")
            raise RuntimeError("Could not locate question input field.")

        question_elem.click()
        time.sleep(0.3)
        # Clear contenteditable thoroughly using keyboard shortcuts
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        time.sleep(0.2)
        question_elem.type(question_text, delay=20)
        time.sleep(0.5)

    def _get_option_inputs(self) -> list:
        """Finds all current answer option input fields."""
        return self.page.query_selector_all(
            "input[placeholder*='Answer' i], "
            "div[contenteditable='true'][aria-label*='Answer' i], "
            "input[aria-label*='Answer' i], "
            "input[placeholder*='Option' i], "
            "input[aria-label*='Option' i], "
            "ytd-poll-choice-editor-renderer input, "
            "div.choice-container input"
        )

    def enter_options(self, options: List[str]):
        """
        Enters 4 quiz options, clicking '+ Add answer' to expand from 2 options to 4.
        """
        if len(options) != 4:
            raise ValueError(f"Expected 4 options, got {len(options)}")

        logger.info("Expanding to 4 answer fields...")
        # Check current inputs count
        inputs = self._get_option_inputs()

        # Click '+ Add answer' button until we have 4 inputs
        for attempt in range(4):
            if len(inputs) >= 4:
                break
            add_btn = self._find_element("add_option_btn", timeout=3000)
            if add_btn:
                try:
                    add_btn.click()
                    time.sleep(0.8)
                    inputs = self._get_option_inputs()
                    logger.info(f"Clicked '+ Add answer' (now {len(inputs)} answer inputs).")
                except Exception as e:
                    logger.debug(f"Click on add answer encountered: {e}")
            else:
                break

        if len(inputs) < 4:
            # Fallback search inside composer dialog
            inputs = self.page.query_selector_all("ytd-post-creation-dialog-renderer input[type='text'], input[placeholder*='Answer' i]")

        if len(inputs) < 4:
            self._save_screenshot("insufficient_option_inputs")
            raise RuntimeError(f"Found only {len(inputs)} answer inputs (expected 4).")

        logger.info(f"Filling {len(options)} options into answer inputs...")
        for idx, opt_text in enumerate(options):
            inp = inputs[idx]
            inp.click()
            time.sleep(0.2)
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")
            inp.type(opt_text, delay=15)
            time.sleep(0.3)

        logger.info("All 4 answers successfully filled.")

    def select_correct_answer(self, correct_index: int):
        """
        Clicks the correct answer checkmark toggle for the designated option.
        Answer 1 (index 0) is often selected by default in YouTube Quiz.
        """
        logger.info(f"Selecting Option {chr(ord('A') + correct_index)} (index {correct_index}) as correct answer.")
        time.sleep(0.5)

        # Answer 1 is already checked green by default. If index 0, we can verify or click
        inputs = self._get_option_inputs()
        if not inputs or correct_index >= len(inputs):
            logger.warning("Could not locate target answer input for answer selection.")
            return

        target_input = inputs[correct_index]

        # Try clicking the checkmark button directly inside the row of target_input
        clicked = False
        try:
            # Look for the checkmark button / SVG in the same container or preceding sibling
            row_btn = target_input.evaluate_handle("""el => {
                const row = el.closest('ytd-poll-choice-editor-renderer, ytd-backstage-quiz-choice-renderer') || el.parentElement.parentElement;
                return row.querySelector('button, yt-icon-button, [role="radio"], [role="checkbox"], svg');
            }""")
            if row_btn:
                row_btn.as_element().click()
                clicked = True
                logger.info(f"Clicked answer checkmark inside row {correct_index + 1}.")
        except Exception as e:
            logger.debug(f"Row checkmark click attempt: {e}")

        if not clicked:
            # Fallback: query all checkmark toggle buttons on the page
            selectors = [
                "button[aria-label*='correct' i]",
                "div[aria-label*='correct' i]",
                "ytd-poll-choice-editor-renderer yt-icon",
                "tp-yt-paper-radio-button",
                "div.correct-answer-select",
            ]
            for sel in selectors:
                targets = self.page.query_selector_all(sel)
                if len(targets) >= 4:
                    targets[correct_index].click()
                    clicked = True
                    logger.info("Clicked correct answer indicator toggle.")
                    break

        time.sleep(0.5)

    def enter_explanation(self, explanation_text: str):
        """Enters the explanation in the 'Add an explanation (optional)' field."""
        if not explanation_text:
            return

        logger.info(f"Entering explanation: '{explanation_text[:40]}...'")
        exp_input = self._find_element("explanation_input", timeout=4000)
        if exp_input:
            exp_input.click()
            time.sleep(0.2)
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")
            exp_input.type(explanation_text, delay=15)
            time.sleep(0.5)
            logger.info("Explanation entered successfully.")
        else:
            logger.info("Explanation field not found or not visible.")

    def publish_button_click(self):
        """Clicks the final 'Post' button to publish the quiz to YouTube."""
        logger.info("Clicking final Publish/Post button...")
        time.sleep(1)
        post_btn = self._find_element("post_btn", timeout=5000)
        if not post_btn:
            self._save_screenshot("post_btn_missing")
            raise RuntimeError("Could not find the 'Post' button to complete publication.")

        post_btn.click()
        time.sleep(4)
        self._save_screenshot("published_result")
        logger.info("Publish button clicked successfully.")

    def publish(
        self,
        quiz: Quiz,
        user_verified: bool,
        dry_run: bool = False,
        channel_id: Optional[str] = None,
    ) -> dict:
        """
        Executes the full publishing flow with strict verification check.
        If dry_run is True, fills out the form completely but stops before clicking 'Post'.
        """
        if not user_verified:
            raise PermissionError("Publishing rejected: User verification checkbox was not checked.")

        if not quiz or not quiz.question:
            raise ValueError("Publishing rejected: Quiz data is invalid or empty.")

        target_channel = channel_id or self.channel_id
        logger.info(f"Initiating quiz publishing for channel '{target_channel}' (dry_run={dry_run})...")

        try:
            self.open_youtube()
            self.open_create_post(channel_id=target_channel)
            self.select_quiz()
            self.enter_question(quiz.question)
            self.enter_options(quiz.options)
            self.select_correct_answer(quiz.correct_answer)
            self.enter_explanation(quiz.explanation)

            if dry_run:
                self._save_screenshot("dry_run_completed")
                logger.info("Dry run completed: Quiz filled in browser without clicking Post.")
                return {
                    "success": True,
                    "mode": "dry_run",
                    "message": "Quiz form populated in browser. Final publication skipped in dry-run mode.",
                }

            self.publish_button_click()
            logger.info("Quiz successfully published to YouTube Community!")
            return {
                "success": True,
                "mode": "published",
                "message": "Quiz has been successfully published to YouTube Community!",
            }

        except Exception as e:
            self._save_screenshot("publish_error")
            logger.error(f"Publishing failed: {e}")
            raise
        finally:
            # We keep the browser open briefly or close according to manager
            if self.browser_manager.headless:
                self.browser_manager.close()
