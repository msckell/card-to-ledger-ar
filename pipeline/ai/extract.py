"""AI use 1: read each receipt and return vendor, date, amount and currency.

The model reads the text layer of the PDF. It returns what the document shows, nothing
converted. The engine then checks the amount against the transaction: a difference becomes
an exception, never a silent fix. Outputs are committed to data/ai/extract.json and reused
while the receipt text and the prompt do not change.
"""

from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from typing import Literal

from pydantic import BaseModel, Field

from pipeline.ai import llm
from pipeline.ai.store import load, save, workers
from pipeline.receipt_text import receipt_ids, text

SYSTEM = """You read one receipt or invoice and return four fields exactly as the document shows them.

- vendor: the business or person that issued the document, as printed.
- date: the date of the charge in YYYY-MM-DD. Use the payment or issue date. For a hotel folio use \
the departure date. Spanish documents write dates as day/month/year.
- amount: the final total of the document as a plain decimal with a dot and two decimals, no \
thousands separators. If a tip line is left blank, the printed total is the amount.
- currency: USD, EUR, ARS or USDC. "US$" is USD. "$" on a document in Argentine pesos is ARS. \
"$" on an English receipt from the United States is USD. If no currency is printed at all, use \
the currency of the country in the issuer's address when that is clear (a street address in the \
United States means USD), otherwise null.

Do not convert currencies, do not add or subtract anything, do not guess. Use null for a \
field the document does not show."""


class ReceiptFields(BaseModel):
    vendor: str | None = Field(description="Issuer name as printed")
    date: str | None = Field(description="YYYY-MM-DD", pattern=r"^\d{4}-\d{2}-\d{2}$")
    amount: str | None = Field(description="Final total, e.g. 1234.56", pattern=r"^\d+\.\d{2}$")
    currency: Literal["USD", "EUR", "ARS", "USDC"] | None


def _key(rid: str) -> str:
    return hashlib.sha256((SYSTEM + llm.model_name("extract") + text(rid)).encode()).hexdigest()[:16]


def _one(rid: str) -> tuple[str, dict]:
    try:
        r = llm.ask("extract", SYSTEM, f"Receipt {rid}, text layer:\n\n{text(rid)}", ReceiptFields, 600)
    except llm.LlmError as exc:
        llm.failed_call("extract")
        return rid, {"error": str(exc), "key": _key(rid)}
    return rid, {**r.data.model_dump(), "key": _key(rid), "model": r.model, "duration_s": r.duration_s}


def run(limit: int | None = None) -> dict:
    store = load("extract.json") or {"receipts": {}}
    done = store["receipts"]
    todo = [rid for rid in receipt_ids()
            if rid not in done or done[rid].get("error") or done[rid].get("key") != _key(rid)]
    if limit:
        todo = todo[:limit]
    with ThreadPoolExecutor(max_workers=workers()) as pool:
        for rid, out in pool.map(_one, todo):
            done[rid] = out
    store["receipts"] = dict(sorted(done.items()))
    store["model"] = llm.model_name("extract")
    store["backend"] = llm.backend()
    save("extract.json", store)
    return {"called": len(todo), "errors": sum(1 for v in done.values() if v.get("error")), "total": len(done)}
