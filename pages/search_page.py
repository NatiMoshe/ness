from urllib.parse import urlencode

import allure
from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.price_parser import parse_price, is_non_usd


class SearchPage(BasePage):
    _SEARCH_URL = "https://www.ebay.com/sch/i.html"

    # eBay search result selectors
    _ITEM = "ul.srp-results > li"
    _ITEM_LINK = "a.s-item__link"
    _ITEM_LINK_FALLBACKS = ["a.s-item__link", "a[href*='/itm/']", "a[href*='ebay.com/itm']"]
    _ITEM_PRICE_FALLBACKS = [
        "[class*='price']",
        ".s-item__price",
        ".x-price-primary span",
        "[data-testid*='price']",
    ]
    _ITEM_TITLE = "[class*='title']"
    _ITEM_TITLE_FALLBACKS = ["[class*='title']", ".s-item__title", "h3"]
    _NEXT_PAGE = "a.pagination__next"
    _MAX_PAGES = 3

    # Sidebar price filter
    _PRICE_MAX_INPUT = "input[aria-label*='aximum']"
    _PRICE_FILTER_SUBMIT = ".x-refine__go-btn"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    @allure.step("Search '{query}' with max price ${max_price}, collecting up to {limit} results")
    def search_items_by_name_under_price(
        self, query: str, max_price: float, limit: int = 5
    ) -> list[str]:
        """Return up to `limit` item URLs priced at or below `max_price`.

        Uses eBay's URL-level price filter for efficiency, then validates each
        displayed price and follows pagination until `limit` is reached.
        """
        self._navigate_with_price_filter(query, max_price)
        self._apply_sidebar_price_filter(max_price)

        urls: list[str] = []
        page_num = 1

        while len(urls) < limit and page_num <= self._MAX_PAGES:
            allure.attach(
                self._page.url,
                name=f"Search page {page_num} URL",
                attachment_type=allure.attachment_type.TEXT,
            )
            new_urls = self._collect_items_from_page(max_price, remaining=limit - len(urls))
            urls.extend(new_urls)

            if len(urls) >= limit:
                break

            if not self._go_to_next_page():
                break
            page_num += 1

        result = urls[:limit]
        allure.attach(
            "\n".join(result) if result else "No items found",
            name=f"Collected {len(result)} item URLs",
            attachment_type=allure.attachment_type.TEXT,
        )
        self.take_screenshot(f"search_results_{query}")
        return result

    def _navigate_with_price_filter(self, query: str, max_price: float) -> None:
        params = urlencode(
            {
                "_nkw": query,
                "_udhi": int(max_price),
                "_sop": "15",
            }
        )
        self.navigate(f"{self._SEARCH_URL}?{params}")
        self._handle_bot_challenge()
        self._dismiss_overlay()

    def _apply_sidebar_price_filter(self, max_price: float) -> None:
        """Attempt to set the sidebar max-price input for an extra filter layer."""
        try:
            max_input = self._page.locator(self._PRICE_MAX_INPUT).first
            max_input.wait_for(state="visible", timeout=4_000)
            max_input.fill(str(int(max_price)))
            submit = self._page.locator(self._PRICE_FILTER_SUBMIT).first
            submit.click(timeout=4_000)
            self._page.wait_for_load_state("load", timeout=10_000)
        except Exception:
            pass

    def _collect_items_from_page(self, max_price: float, remaining: int) -> list[str]:
        try:
            self._page.locator(self._ITEM).first.wait_for(state="visible", timeout=8_000)
        except Exception:
            pass

        collected: list[str] = []
        skipped_reasons: list[str] = []
        items = self._page.locator(self._ITEM).all()

        allure.attach(
            f"URL: {self._page.url}\nitem count: {len(items)}",
            name="Page diagnostic",
            attachment_type=allure.attachment_type.TEXT,
        )
        for item in items:
            if len(collected) >= remaining:
                break
            try:
                title = self._get_title_text(item)
                if not title or title in ("Shop on eBay",):
                    continue

                price_text = self._get_price_text(item)
                if price_text is None:
                    skipped_reasons.append(f"no price selector matched for '{title[:40]}'")
                    continue

                if is_non_usd(price_text) or parse_price(price_text) <= max_price:
                    href = self._get_item_href(item)
                    if href:
                        collected.append(href)
                else:
                    skipped_reasons.append(
                        f"price {parse_price(price_text)} > {max_price} for '{title[:40]}'"
                    )
            except Exception as exc:
                skipped_reasons.append(f"exception: {exc}")
                continue

        if skipped_reasons:
            allure.attach(
                "\n".join(skipped_reasons[:20]),
                name="Skipped items (debug)",
                attachment_type=allure.attachment_type.TEXT,
            )
        return collected

    def _get_title_text(self, item) -> str | None:
        for selector in self._ITEM_TITLE_FALLBACKS:
            try:
                el = item.locator(selector).first
                text = el.text_content(timeout=500)
                if text and text.strip():
                    return text.strip()
            except Exception:
                continue
        return None

    def _get_item_href(self, item) -> str | None:
        for selector in self._ITEM_LINK_FALLBACKS:
            try:
                href = item.locator(selector).first.get_attribute("href", timeout=1_000)
                if href and href.startswith("http"):
                    return href
            except Exception:
                continue
        return None

    def _get_price_text(self, item) -> str | None:
        for selector in self._ITEM_PRICE_FALLBACKS:
            try:
                el = item.locator(selector).first
                text = el.text_content(timeout=500)
                if text and text.strip():
                    return text.strip()
            except Exception:
                continue
        return None

    def _go_to_next_page(self) -> bool:
        try:
            next_btn = self._page.locator(self._NEXT_PAGE).first
            next_btn.wait_for(state="visible", timeout=3_000)
            if not next_btn.is_enabled():
                return False
            next_btn.click()
            self._page.wait_for_load_state("load", timeout=10_000)
            self._handle_bot_challenge()
            return True
        except Exception:
            return False
