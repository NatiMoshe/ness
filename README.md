# eBay E2E Automation — Playwright + Python

Automates the eBay shopping flow: search with a price filter → add items to cart → verify the total doesn't exceed the budget.

---

## Prerequisites

- Python 3.11+
- Java 11+ (required by Allure CLI)
- Allure CLI — install once:
  - **Windows (Scoop):** `scoop install allure`
  - **Mac (Homebrew):** `brew install allure`
  - **Manual:** download from [github.com/allure-framework/allure2/releases](https://github.com/allure-framework/allure2/releases), extract, add `bin/` to PATH

---

## How to Run

**Create and activate a virtual environment:**
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
playwright install chromium
```

**Run the tests:**
```bash
pytest -v
```

**Run with Allure reporting:**
```bash
pytest --alluredir=allure-results -v
allure serve allure-results
```

`allure serve` generates the report and opens it in your browser automatically.

**Headless mode (CI):**
```bash
HEADLESS=true pytest -v
```

Test inputs (search query, max price, item limit) live in `config/test_data.json`. You can also override via environment variables: `HEADLESS`, `SLOW_MO`, `EBAY_USERNAME`, `EBAY_PASSWORD`.

---

## Architecture

The project follows the **Page Object Model** — one class per eBay page, all locators and interactions kept inside that class. Tests only orchestrate; they don't touch selectors directly.

```
pages/
  base_page.py     # shared helpers: navigate, screenshot, overlay dismissal, bot-challenge wait
  login_page.py    # guest login flow
  search_page.py   # search + URL price filter + sidebar filter + pagination
  item_page.py     # variant selection + add to cart
  cart_page.py     # open cart + read subtotal + assert total

tests/
  test_ebay_e2e.py # three test cases wiring the 4 core functions

config/
  test_data.json   # all test inputs (data-driven)

utils/
  price_parser.py  # handles "$12.99", "$10 to $25", ILS, etc.
  config_loader.py # loads test_data.json, ENV vars take precedence
```

Every meaningful action attaches a screenshot and an Allure step, so failures are easy to diagnose.

---

## Limitations & Assumptions

- **Guest mode by default.** Credentials are empty in `test_data.json`, so tests run as a guest. eBay guest cart works for most items but is less stable than a logged-in session. Fill in `EBAY_USERNAME` / `EBAY_PASSWORD` to run logged in.

- **Bot detection.** eBay blocks automated traffic aggressively. The tests run with `headless=false` and a small delay between actions to reduce this. If you hit consistent blocks, a residential proxy is the next step.

- **ILS currency.** From an Israeli IP, eBay shows prices in ILS. The `max_price` in `test_data.json` should be set in ILS accordingly (e.g. 800 ILS for shoes instead of $220 USD).

- **Variant selection is random.** When an item has size/color options, a random available choice is picked. Some combinations may be out of stock; those items are skipped and logged.

- **Auction-only items are skipped.** If there's no "Add to cart" button (only "Place bid"), the item is logged and skipped.

- **Price ranges.** Items shown as "$10–$25" are evaluated on the lower bound. The actual price added to cart depends on the chosen variant.
