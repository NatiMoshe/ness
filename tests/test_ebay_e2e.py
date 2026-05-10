"""
eBay E2E test suite.

Flow per scenario:
  1. Login (or guest)
  2. searchItemsByNameUnderPrice  -> collect up to N item URLs
  3. addItemsToCart               -> add each item, handle variants
  4. assertCartTotalNotExceeds    -> verify cart subtotal <= budget
"""

import pytest
import allure
from playwright.sync_api import Page

from pages.login_page import LoginPage
from pages.search_page import SearchPage
from pages.item_page import ItemPage
from pages.cart_page import CartPage


def _scenarios(config: dict) -> list[dict]:
    return config.get("scenarios", [])


@allure.epic("eBay E2E")
@allure.feature("Shopping flow")
class TestEbayE2E:

    @allure.story("Full shopping flow - search, add to cart, verify total")
    @pytest.mark.parametrize("scenario_idx", [0])
    def test_full_flow(self, page: Page, config: dict, scenario_idx: int) -> None:
        scenarios = _scenarios(config)
        assert scenarios, "No test scenarios defined in test_data.json"
        scenario = scenarios[scenario_idx]

        query: str = scenario["query"]
        max_price: float = float(scenario["max_price"])
        limit: int = int(scenario.get("limit", 5))
        credentials = config.get("credentials", {})

        allure.dynamic.title(f"eBay: '{query}' under ${max_price}")
        allure.dynamic.description(
            f"Search for '{query}', filter by max price ${max_price}, "
            f"collect up to {limit} items, add to cart, assert total."
        )

        # Step 1 - authentication
        login_page = LoginPage(page)
        if credentials.get("username") and credentials.get("password"):
            login_page.login(credentials["username"], credentials["password"])
        else:
            login_page.login_as_guest()

        # Step 2 - search with price filter
        search_page = SearchPage(page)
        urls = search_page.search_items_by_name_under_price(query, max_price, limit)

        assert len(urls) > 0, (
            f"No items found for query='{query}' under ${max_price}. "
            "Check connectivity and eBay availability."
        )

        # Step 3 - add items to cart
        item_page = ItemPage(page)
        item_page.add_items_to_cart(urls)

        # Step 4 - assert cart total
        cart_page = CartPage(page)
        cart_page.assert_cart_total_not_exceeds(
            budget_per_item=max_price,
            items_count=len(urls),
        )

    @allure.story("searchItemsByNameUnderPrice - unit-level smoke")
    def test_search_returns_urls(self, page: Page, config: dict) -> None:
        scenario = _scenarios(config)[0]
        LoginPage(page).login_as_guest()
        search_page = SearchPage(page)
        urls = search_page.search_items_by_name_under_price(
            query=scenario["query"],
            max_price=float(scenario["max_price"]),
            limit=2,
        )
        assert isinstance(urls, list)
        assert len(urls) > 0, (
            f"Search returned no URLs for query='{scenario['query']}' under "
            f"${scenario['max_price']}. Check eBay selectors or connectivity."
        )
        assert all(u.startswith("http") for u in urls)

    @allure.story("assertCartTotalNotExceeds - validates subtotal reading")
    @pytest.mark.skip(reason="Requires items already in cart; run after test_full_flow")
    def test_assert_cart_standalone(self, page: Page, config: dict) -> None:
        scenario = _scenarios(config)[0]
        cart_page = CartPage(page)
        cart_page.assert_cart_total_not_exceeds(
            budget_per_item=float(scenario["max_price"]),
            items_count=int(scenario["limit"]),
        )
