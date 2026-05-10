import allure
from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.price_parser import parse_price


class CartPage(BasePage):
    URL = "https://cart.ebay.com/"

    _CART_ICON_SELECTORS = [
        "#gh-cart-n",
        "a[href*='/cart']",
        "[data-testid='gh-cart']",
        "#cartSummaryLink",
    ]

    _SUBTOTAL_SELECTORS = [
        "[class*='total']",
        "[class*='subtotal']",
        ".order-summary__total-price",
        "[id*='subtotal'] .bold",
        ".cart-bucket-subtotal .gh-price",
        "span[id*='subtotal']",
        ".summary-subtotal-amount",
        "[class*='total-price']",
        "[class*='order-total']",
    ]

    _CART_ITEM = ".cart-item"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    @allure.step("Assert cart total <= ${budget_per_item} x {items_count}")
    def assert_cart_total_not_exceeds(
        self, budget_per_item: float, items_count: int
    ) -> None:
        """Open cart, read subtotal, assert it does not exceed budget_per_item * items_count."""
        self._open_cart()
        self._dismiss_overlay()

        total = self._read_cart_total()
        threshold = budget_per_item * items_count

        allure.attach(
            f"Cart total: ${total:.2f}\nThreshold: ${threshold:.2f} (${budget_per_item} x {items_count})",
            name="Cart total assertion",
            attachment_type=allure.attachment_type.TEXT,
        )
        self.take_screenshot("cart_final")

        assert total <= threshold, (
            f"Cart total ${total:.2f} exceeds budget threshold ${threshold:.2f} "
            f"(${budget_per_item} x {items_count} items)"
        )

    def _open_cart(self) -> None:
        """Navigate to the cart. Falls back to clicking the header cart icon if
        the direct URL redirects to an error page (common for guest sessions)."""
        self.navigate(self.URL)
        self._handle_bot_challenge(timeout=20_000)
        if any(p in self._page.url for p in ("/n/error", "/signin", "/splashui/")):
            cart_btn = self._first_visible(self._CART_ICON_SELECTORS, timeout=5_000)
            if cart_btn:
                cart_btn.click()
                self._page.wait_for_load_state("domcontentloaded", timeout=15_000)
                self._handle_bot_challenge()

    def _read_cart_total(self) -> float:
        """Read cart subtotal by scanning all candidate elements for a parseable price."""
        self._page.wait_for_load_state("domcontentloaded", timeout=10_000)
        for selector in self._SUBTOTAL_SELECTORS:
            try:
                for el in self._page.locator(selector).all():
                    txt = el.text_content(timeout=1_000)
                    if not txt:
                        continue
                    price = parse_price(txt.strip())
                    if 0 < price < float("inf"):
                        allure.attach(
                            f"selector={selector!r}  raw={txt.strip()!r}  parsed={price}",
                            name="Cart total found",
                            attachment_type=allure.attachment_type.TEXT,
                        )
                        return price
            except Exception:
                continue
        raise RuntimeError(
            "Could not locate cart subtotal element. "
            "Verify cart page loaded and credentials are valid."
        )
