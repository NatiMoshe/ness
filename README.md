# eBay E2E Automation — Playwright + Python

End-to-end automation for eBay shopping flow: search with price filter → add to cart → assert total.

---

## Architecture

```
.
├── config/
│   └── test_data.json       # Data-Driven: all test inputs (query, max_price, limit, credentials)
├── pages/                   # Page Object Model
│   ├── base_page.py         # BasePage: navigate, screenshot, shared locator helpers
│   ├── login_page.py        # LoginPage: eBay sign-in or guest mode
│   ├── search_page.py       # SearchPage: search + price filter + pagination
│   ├── item_page.py         # ItemPage: variant selection + add to cart
│   └── cart_page.py         # CartPage: subtotal reading + assertion
├── tests/
│   └── test_ebay_e2e.py     # Pytest test class — orchestrates the 4 core functions
├── utils/
│   ├── config_loader.py     # Loads test_data.json; ENV vars override config
│   └── price_parser.py      # Parses eBay price strings ($12.99, $10 to $25, etc.)
├── screenshots/             # Per-action PNG screenshots (also attached to Allure)
├── allure-results/          # Allure raw JSON (generate HTML report with allure serve)
├── conftest.py              # Session-scoped browser + function-scoped page fixtures
├── pytest.ini               # Test runner config
└── requirements.txt
```

### Design Patterns

| Pattern | Where applied |
|---------|---------------|
| **Page Object Model (POM)** | One class per eBay page, each encapsulates all locators and interactions for that page |
| **OOP / SRP** | BasePage provides shared utilities; subclasses only contain page-specific logic |
| **Data-Driven** | All test parameters live in `config/test_data.json`; override via ENV for CI profiles |
| **Allure reporting** | `@allure.step`, `allure.attach` on every meaningful action; screenshots embedded |

---

## Prerequisites

- Python 3.11+
- Node.js (required internally by Playwright)

```bash
pip install -r requirements.txt
playwright install chromium
```

---

## Running the Tests

```bash
# Run all tests
pytest

# Run headless (CI mode)
HEADLESS=true pytest

# Run a specific scenario index
pytest tests/test_ebay_e2e.py::TestEbayE2E::test_full_flow

# With Allure report
pytest
allure serve allure-results
```

### ENV Variable Overrides

| Variable | Description | Example |
|----------|-------------|---------|
| `HEADLESS` | Run browser headless | `HEADLESS=true` |
| `SLOW_MO` | Milliseconds between actions | `SLOW_MO=0` |
| `EBAY_USERNAME` | eBay account username | `EBAY_USERNAME=me@email.com` |
| `EBAY_PASSWORD` | eBay account password | `EBAY_PASSWORD=secret` |
| `TEST_CONFIG_PATH` | Override config file path | `TEST_CONFIG_PATH=/ci/config.json` |

---

## Limitations & Assumptions

**Authentication / Guest Mode**  
If `credentials.username` and `credentials.password` are empty in `test_data.json` (the default), the test runs as a guest. eBay supports guest cart for most items. Set `EBAY_USERNAME` / `EBAY_PASSWORD` for a logged-in session, which is more reliable for cart total reading.

**Currency**  
Prices are parsed assuming USD (`$`). Adjust `utils/price_parser.py` if running against a non-USD eBay domain.

**eBay Bot Detection**  
eBay uses bot-detection heuristics. Running with `headless=false` and a realistic `slow_mo` (default 400 ms) reduces blocking. If requests are consistently blocked, a residential proxy may be needed.

**Variant Selection**  
Variants (size, color) are picked randomly from available options. Some items may require a specific combination that's in stock — the test logs and skips any item where "Add to cart" is not reachable after variant selection.

**Auction-Only Items**  
Items with only a "Bid" option (no "Add to cart") are skipped with a logged warning.

**Price Range Items**  
Items displayed as "$10.00 to $25.00" are evaluated against the lower bound. If the lower bound ≤ `max_price`, the URL is included; the actual added price depends on the variant chosen.

---

## Allure Report

After running the tests:

```bash
allure serve allure-results
```

Each Allure report includes:
- Step-by-step breakdown of each function
- Screenshots embedded at every key action
- Item URLs collected, cart total, and assertion details
