import os
import time
from pathlib import Path

import allure
from playwright.sync_api import Page, Locator


class BasePage:
    SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots"

    def __init__(self, page: Page) -> None:
        self._page = page
        self.SCREENSHOTS_DIR.mkdir(exist_ok=True)

    def navigate(self, url: str) -> None:
        self._page.goto(url, wait_until="domcontentloaded", timeout=60_000)

    def take_screenshot(self, name: str) -> None:
        safe_name = name.replace("/", "_").replace(":", "_")
        path = self.SCREENSHOTS_DIR / f"{safe_name}_{int(time.time())}.png"
        self._page.screenshot(path=str(path), full_page=False)
        with open(path, "rb") as f:
            allure.attach(f.read(), name=name, attachment_type=allure.attachment_type.PNG)

    def _first_visible(self, selectors: list[str], timeout: int = 5_000) -> Locator | None:
        """Return the first locator from a list that is visible on the page."""
        for selector in selectors:
            loc = self._page.locator(selector).first
            try:
                loc.wait_for(state="visible", timeout=timeout)
                return loc
            except Exception:
                continue
        return None

    def _handle_bot_challenge(self, timeout: int = 15_000) -> None:
        """Wait for eBay's bot-challenge or captcha page to resolve itself."""
        if not any(p in self._page.url for p in ("/splashui/challenge", "/splashui/captcha")):
            return
        allure.attach(
            self._page.url,
            name="Bot challenge detected — waiting for resolution",
            attachment_type=allure.attachment_type.TEXT,
        )
        try:
            self._page.wait_for_url(
                lambda url: "/splashui/challenge" not in url and "/splashui/captcha" not in url,
                timeout=timeout,
            )
            self._page.wait_for_load_state("domcontentloaded", timeout=15_000)
        except Exception:
            pass

    def _dismiss_overlay(self) -> None:
        """Close common cookie/sign-in overlays that block interaction."""
        dismiss_selectors = [
            "button#gdpr-banner-accept",
            "[data-testid='signin-layer-close']",
            "button[aria-label='Close']",
            "#miniModal [aria-label='Close']",
        ]
        for selector in dismiss_selectors:
            loc = self._page.locator(selector)
            if loc.count() > 0:
                try:
                    loc.first.click(timeout=2_000)
                    self._page.wait_for_timeout(500)
                except Exception:
                    pass
