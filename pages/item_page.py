import random

import allure
from playwright.sync_api import Page

from pages.base_page import BasePage


class ItemPage(BasePage):
    _ADD_TO_CART_SELECTORS = [
        "#atcRedesignId_btn",
        "[data-testid='ux-call-to-action'][aria-label*='cart' i]",
        "a[aria-label*='Add to cart' i]",
        "button:has-text('Add to cart')",
        "a:has-text('Add to cart')",
    ]

    _VARIANT_SELECT = "select.msku-sel"
    _VARIANT_BUTTON_GROUP_SELECTORS = [
        "[data-testid='x-msku-v2']",
        "[data-testid='x-msku']",
    ]
    _VARIANT_BTN_AVAILABLE = (
        "button:not([aria-disabled='true']):not(.btn-disabled):not([disabled])"
    )

    _MODAL_GO_TO_CART = "button:has-text('Go to cart')"
    _MODAL_CONTINUE = "button:has-text('Continue shopping')"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    @allure.step("Add items to cart")
    def add_items_to_cart(self, urls: list[str]) -> None:
        for idx, url in enumerate(urls, start=1):
            with allure.step(f"Item {idx}/{len(urls)}: {url}"):
                self._add_single_item(idx, url)

    def _add_single_item(self, idx: int, url: str) -> None:
        self.navigate(url)
        self._dismiss_overlay()
        self._select_random_variants()

        btn = self._first_visible(self._ADD_TO_CART_SELECTORS, timeout=6_000)
        if btn is None:
            allure.attach(
                f"No 'Add to cart' button found on {url}",
                name=f"Item {idx} skipped",
                attachment_type=allure.attachment_type.TEXT,
            )
            self.take_screenshot(f"item_{idx}_skipped")
            return

        btn.click()
        self._page.wait_for_timeout(1_500)
        self._handle_post_add_modal()
        self.take_screenshot(f"item_{idx}_added_to_cart")

    def _select_random_variants(self) -> None:
        """Pick a random available option for every variant dimension on the page."""
        # Wait for the page to finish rendering variant sections before querying.
        self._page.wait_for_load_state("domcontentloaded", timeout=10_000)

        selects = self._page.locator(self._VARIANT_SELECT).all()
        for sel in selects:
            try:
                sel.wait_for(state="visible", timeout=3_000)
                options = sel.locator("option:not([disabled]):not([value=''])").all()
                if options:
                    chosen = random.choice(options)
                    sel.select_option(value=chosen.get_attribute("value"))
                    self._page.wait_for_timeout(500)
            except Exception:
                continue

        # Try each known button-group selector pattern; stop after the first that
        # yields groups so we don't double-click a size that was already selected.
        for group_selector in self._VARIANT_BUTTON_GROUP_SELECTORS:
            try:
                first_group = self._page.locator(group_selector).first
                first_group.wait_for(state="visible", timeout=3_000)
            except Exception:
                continue

            groups = self._page.locator(group_selector).all()
            for group in groups:
                try:
                    available = group.locator(self._VARIANT_BTN_AVAILABLE).all()
                    if available:
                        random.choice(available).click()
                        self._page.wait_for_timeout(600)
                except Exception:
                    continue
            break  # matched a selector pattern; don't try the next one

    def _handle_post_add_modal(self) -> None:
        """Dismiss the post-add confirmation modal."""
        # Prefer "Continue shopping" to stay on the item-browsing flow.
        # Fall back to "Go to cart" if that's the only dismiss option available.
        for selector in (self._MODAL_CONTINUE, self._MODAL_GO_TO_CART):
            try:
                btn = self._page.locator(selector).first
                btn.wait_for(state="visible", timeout=4_000)
                btn.click()
                return
            except Exception:
                continue
