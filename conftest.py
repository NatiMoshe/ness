import pytest
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from utils.config_loader import ConfigLoader


@pytest.fixture(scope="session")
def config() -> dict:
    return ConfigLoader.load()


@pytest.fixture(scope="session")
def browser(config: dict) -> Browser:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=config.get("headless", False),
            slow_mo=config.get("slow_mo", 400),
            args=["--no-sandbox", "--disable-dev-shm-usage", "--ignore-certificate-errors"],
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser) -> BrowserContext:
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/136.0.0.0 Safari/537.36"
        ),
        locale="en-US",
        timezone_id="America/New_York",
        geolocation={"latitude": 40.7128, "longitude": -74.0060},
        permissions=["geolocation"],
    )
    yield ctx
    ctx.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Page:
    p = context.new_page()
    yield p
    p.close()
