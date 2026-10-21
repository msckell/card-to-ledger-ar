"""Money as integer cents. Decimal only for rates. Rounding happens once, here."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def to_cents(amount: str | Decimal) -> int:
    """'1234.5' -> 123450. Refuses anything that is not an exact cent amount."""
    value = Decimal(str(amount))
    cents = value * 100
    if cents != cents.to_integral_value():
        raise ValueError(f"amount has more than 2 decimals: {amount}")
    return int(cents)


def cents_str(cents: int) -> str:
    """123450 -> '1234.50' (machine format, used in JSON)."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"


def convert(cents: int, rate: Decimal) -> int:
    """Foreign cents times a rate, rounded half up to whole cents of the other currency."""
    return int((Decimal(cents) * rate).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def fmt(cents: int, symbol: str = "") -> str:
    """Display format with thousands separators: 123450 -> '1,234.50'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    whole = f"{cents // 100:,}"
    return f"{sign}{symbol}{whole}.{cents % 100:02d}"
