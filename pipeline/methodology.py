"""Every assumption behind the close, labeled documented, assumption or out of scope.

Used by the Excel `Metodología` sheet and by the page.
"""

from __future__ import annotations

from pipeline import fx
from pipeline.config import settings


def items() -> list[dict]:
    s = settings()
    src = fx.source_record()
    downloaded = src["downloaded_at"][:10]
    return [
        {
            "topic": "Exchange rate source",
            "label": "documented",
            "detail": (
                f"Official USD/ARS series from ArgentinaDatos ({s['fx']['source_url']}), "
                f"downloaded {downloaded} and frozen in data/fx/usd_ars_oficial.csv. "
                "The build reads only the snapshot."
            ),
        },
        {
            "topic": "Which rate and which day",
            "label": "assumption",
            "detail": (
                f"Seller rate ({s['fx']['rate_side']}) on the posting date of each movement: official "
                "for dollar card spend, crypto dollar for USDC. "
                "To validate with an accountant: buyer rate for assets, transaction date versus "
                "posting date, and Banco Nación versus BCRA Comunicación A 3500."
            ),
        },
        {
            "topic": "Weekend and holiday rates",
            "label": "assumption",
            "detail": "The source publishes a value for every calendar day. The build uses it as published.",
        },
        {
            "topic": "USDC valuation",
            "label": "assumption",
            "detail": (
                "USDC is valued at the crypto dollar seller rate of each day "
                f"({s['fx']['crypto_source_url']}), the rate at which it can be turned into pesos. "
                "One USDC is treated as one crypto dollar. Dollar card spend stays at the official "
                "rate. Whether USDC should be valued at the crypto, MEP or official rate is a question "
                "for the accountant."
            ),
        },
        {
            "topic": "ARS top ups",
            "label": "documented",
            "detail": (
                "USDC received is computed from the ARS sent at the crypto dollar seller rate of "
                "that day and booked at the same rate. Only the rounding the exchange keeps goes "
                "to Diferencias de cambio."
            ),
        },
        {
            "topic": "Month end remeasurement",
            "label": "assumption",
            "detail": (
                "Cuenta USDC is remeasured at the crypto dollar seller rate of the last day of the "
                "month and Tarjeta corporativa a pagar at the official seller rate of that day. "
                "Paying the card with USDC moves the gap between the two rates to Diferencias de "
                "cambio, and so does each remeasurement."
            ),
        },
        {
            "topic": "Opening balances",
            "label": "assumption",
            "detail": (
                f"Synthetic opening balances as of {s['opening_balances']['as_of']}, valued at that "
                "day's crypto seller rate for USDC and official seller rate for the card payable."
            ),
        },
        {
            "topic": "Items in review",
            "label": "documented",
            "detail": (
                "Every movement with an open exception is posted to Partidas pendientes de "
                "imputación until a person resolves it. The entry still balances."
            ),
        },
        {
            "topic": "Rounding",
            "label": "documented",
            "detail": (
                "Amounts are integer cents. Each converted amount is rounded half up to the cent "
                "once, and both sides of a line use the same rounded value."
            ),
        },
        {
            "topic": "Transaction export format",
            "label": "assumption",
            "detail": "The export schema is invented for this prototype. It is not a real API.",
        },
        {
            "topic": "Company and transactions",
            "label": "assumption",
            "detail": (
                "Andes Labs SRL is fictional. All transactions and receipts are synthetic, generated "
                "with a fixed seed together with the correct answer for each one."
            ),
        },
        {
            "topic": "Taxes",
            "label": "out of scope",
            "detail": "No VAT, withholdings or perceptions. Receipt tax lines are part of the cost.",
        },
        {
            "topic": "Posting to a local accounting system",
            "label": "out of scope",
            "detail": "The entry is delivered as Excel. No import file for a specific local system yet.",
        },
    ]
