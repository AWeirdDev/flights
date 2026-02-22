from __future__ import annotations

import re
from datetime import date
from typing import List
from urllib.parse import quote_plus

from .hotels_schema import Hotel, HotelResult


# Currency code → symbol mapping for price regex matching
_CURRENCY_SYMBOLS = {
    "USD": r"\$",
    "EUR": r"€",
    "GBP": r"£",
    "JPY": r"¥",
    "CAD": r"CA\$",
    "AUD": r"A\$",
}

# Noise strings that indicate a regex match is a CSS/JS artifact, not a hotel
_NOISE = frozenset(["{", "Loading", "Sponsored", "font-smooth", "VfPpkd", "$"])


def get_hotels(
    location: str,
    checkin: str,
    checkout: str,
    adults: int = 2,
    currency: str = "USD",
) -> HotelResult:
    """Search Google Hotels and return structured results.

    Args:
        location: Hotel search location (e.g. "Lisbon Portugal").
        checkin: Check-in date in YYYY-MM-DD format.
        checkout: Check-out date in YYYY-MM-DD format.
        adults: Number of adult guests (default: 2).
        currency: Currency code for prices (default: "USD").
            Supported: USD, EUR, GBP, JPY, CAD, AUD.

    Returns:
        HotelResult containing a list of Hotel objects sorted by price.

    Raises:
        ValueError: If checkout is not after checkin.
        RuntimeError: If the Google Hotels request fails.

    Example::

        from fast_flights import get_hotels

        result = get_hotels(
            location="Lisbon Portugal",
            checkin="2026-06-03",
            checkout="2026-06-06",
            adults=2,
        )
        for hotel in result.hotels:
            print(f"{hotel.name} — ${hotel.price_per_night}/night ({hotel.stars}★ {hotel.rating}/5)")
    """
    import primp
    from selectolax.parser import HTMLParser

    # Validate dates
    checkin_date = date.fromisoformat(checkin)
    checkout_date = date.fromisoformat(checkout)
    nights = (checkout_date - checkin_date).days
    if nights <= 0:
        raise ValueError(f"checkout ({checkout}) must be after checkin ({checkin})")

    # Build URL with proper encoding for special characters (e.g. "São Paulo")
    url = (
        f"https://www.google.com/travel/hotels"
        f"?q=hotels+in+{quote_plus(location)}"
        f"&checkin={checkin}"
        f"&checkout={checkout}"
        f"&adults={adults}"
        f"&hl=en"
        f"&curr={currency}"
    )

    client = primp.Client(impersonate="chrome_131", verify=False)
    resp = client.get(url)

    if resp.status_code != 200:
        raise RuntimeError(
            f"Google Hotels request failed with status {resp.status_code}"
        )

    tree = HTMLParser(resp.text)

    # Use dynamic currency symbol so non-USD results are matched correctly
    symbol = _CURRENCY_SYMBOLS.get(currency, re.escape(currency))
    pattern = re.compile(
        rf"^(.+?){symbol}(\d+)([\w\.\s]+?)(\d+\.\d+)/5\(([0-9\.]+[K]?)\)·(\d)-star hotel(.*)$"
    )

    hotels: List[Hotel] = []
    seen: set = set()

    for div in tree.css("div"):
        text = div.text(strip=True)
        m = pattern.match(text)
        if not m:
            continue

        name, price_str, source, rating_str, reviews, stars_str, rest = m.groups()
        name = name.strip()

        if name in seen or not (3 < len(name) < 55):
            continue
        if any(noise in name for noise in _NOISE):
            continue

        seen.add(name)
        amenities = [
            a.strip()
            for a in re.split(r"·|\n", rest)
            if a.strip() and len(a.strip()) < 40
        ]

        price_per_night = int(price_str)
        hotels.append(
            Hotel(
                name=name,
                price_per_night=price_per_night,
                total_price=price_per_night * nights,
                currency=currency,
                stars=int(stars_str),
                rating=float(rating_str),
                reviews=reviews.strip(),
                source=source.strip(),
                amenities=amenities[:3],
            )
        )

    hotels.sort(key=lambda h: h.price_per_night)
    return HotelResult(hotels=hotels)
