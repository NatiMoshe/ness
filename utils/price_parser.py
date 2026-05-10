import re

# Currency markers that are not USD. Covers both symbol (₪) and ISO-code
# (ILS) forms since eBay renders them differently by region.
_NON_USD_MARKERS = ("₪", "ILS", "€", "EUR", "£", "GBP", "¥", "JPY", "₩", "KRW",
                    "₹", "INR", "A$", "AU$", "CA$", "C$")


def is_non_usd(price_text: str) -> bool:
    return any(marker in price_text for marker in _NON_USD_MARKERS)


def parse_price(price_text: str) -> float:
    """Parse the lowest price value from an eBay price string.

    Handles: '$12.99', '$1,234.56', '$10.00 to $25.00' (returns lowest), 'Free'
    Returns float('inf') if no price can be parsed.
    """
    cleaned = price_text.replace(",", "")
    matches = re.findall(r"\d+\.?\d*", cleaned)
    if not matches:
        return float("inf")
    return min(float(m) for m in matches)
