import allure
from playwright.sync_api import Page

from pages.base_page import BasePage


class LoginPage(BasePage):
    URL = "https://www.ebay.com/signin/"

    _USERNAME_INPUT = "#userid"
    _CONTINUE_BTN = "#signin-continue-btn"
    _PASSWORD_INPUT = "#pass"
    _SIGNIN_BTN = "#sgnBt"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    @allure.step("Login to eBay")
    def login(self, username: str, password: str) -> None:
        self.navigate(self.URL)
        self._page.locator(self._USERNAME_INPUT).fill(username)
        self._page.locator(self._CONTINUE_BTN).click()
        self._page.locator(self._PASSWORD_INPUT).wait_for(state="visible", timeout=10_000)
        self._page.locator(self._PASSWORD_INPUT).fill(password)
        self._page.locator(self._SIGNIN_BTN).click()
        self._page.wait_for_url("**/ebay.com/**", timeout=15_000)
        self.take_screenshot("after_login")

    @allure.step("Continue as guest (no credentials configured)")
    def login_as_guest(self) -> None:
        """Navigate to eBay homepage without authenticating."""
        self.navigate("https://www.ebay.com")
        self._dismiss_overlay()
        self.take_screenshot("guest_home")
