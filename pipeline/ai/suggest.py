"""AI use 2: suggest one account for each card purchase that no rule covers.

The model sees only transaction facts: the export row and, when one was matched, the
receipt text. It must pick from the allowed expense accounts (an enum) and give a short
reason and a confidence from 0 to 1. It never sees the ground truth. Whether a suggestion is
accepted is decided later by code, against a measured threshold.
"""

from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from pipeline import close as close_mod
from pipeline import engine
from pipeline.ai import llm
from pipeline.ai.store import load, save, workers
from pipeline.config import account_name, ai_allowed_accounts
from pipeline.receipt_text import text

GUIDE = {
    "5.1.01": "advertising, paid media, marketing materials, creative work for campaigns, merch with the logo",
    "5.1.02": "cloud infrastructure and usage based developer services: hosting, APIs billed by usage, "
              "domains, email and SMS delivery",
    "5.1.03": "software subscriptions and licenses (SaaS seats, apps, design and productivity tools)",
    "5.1.04": "work by independent contractors or freelancers abroad, including marketplace escrow for them",
    "5.1.05": "travel: flights, lodging, ground transport, connectivity and lounges while traveling",
    "5.1.06": "meals, coffee, food for the team or clients, and client gifts",
    "5.1.07": "events, meetups and conference tickets",
    "5.1.08": "office supplies, small equipment, printing for the office, coworking passes",
    "5.1.09": "training, books, courses, newsletters and publications",
    "5.1.10": "bank and card fees",
}

SYSTEM = """You help an accountant in Argentina code card expenses of a SaaS company into its chart \
of accounts. For one card transaction, pick exactly one account from the allowed list, give a short \
reason in plain English that cites only facts you were shown, and a confidence from 0 to 1.

Confidence means: the probability that a careful accountant who sees the same facts would pick the \
same account. Use high values only when the facts leave little room for another account. When the \
receipt is missing or the merchant could sell several kinds of things, lower it.

Allowed accounts:
""" + "\n".join(f"- {c} {account_name(c)}: {GUIDE[c]}" for c in ai_allowed_accounts())


Account = Literal[tuple(ai_allowed_accounts())]  # type: ignore[valid-type]


class Suggestion(BaseModel):
    account: Account
    reason: str = Field(max_length=300)
    confidence: float = Field(ge=0, le=1)


def _prompt(t: engine.Txn) -> str:
    lines = [
        f"Transaction {t.id}",
        f"Posted: {t.posted_at.isoformat()}",
        f"Card descriptor: {t.descriptor}",
        f"Amount: {t.currency} {t.raw['amount']}",
        f"Cardholder: {t.cardholder or 'not given'}",
        f"Cardholder memo: {t.memo or 'empty'}",
    ]
    if t.receipt_id:
        lines += ["", f"Matched receipt {t.receipt_id}, text layer:", text(t.receipt_id)]
    else:
        lines += ["", "No receipt was matched to this transaction."]
    return "\n".join(lines)


def candidates() -> list[engine.Txn]:
    """Card purchases with no rule, after receipt matching, so the receipt can be shown."""
    receipts = close_mod.receipt_fields("ai" if load("extract.json") else "template")
    txns = engine.load_export()
    engine.apply_rules(txns)
    engine.match_receipts(txns, receipts)
    return [t for t in txns if t.type == "card_purchase" and not t.rule_id]


def _key(prompt: str) -> str:
    return hashlib.sha256((SYSTEM + llm.model_name("suggest") + prompt).encode()).hexdigest()[:16]


def _one(item: tuple[str, str, str]) -> tuple[str, dict]:
    tid, sid, prompt = item
    try:
        r = llm.ask("suggest", SYSTEM, prompt, Suggestion, 1500)
    except llm.LlmError as exc:
        llm.failed_call("suggest")
        return tid, {"id": sid, "error": str(exc), "key": _key(prompt)}
    conf = str(Decimal(str(r.data.confidence)).quantize(Decimal("0.01")))
    return tid, {"id": sid, "account": r.data.account, "account_name": account_name(r.data.account),
                 "reason": r.data.reason, "confidence": conf, "key": _key(prompt), "model": r.model}


def run() -> dict:
    store = load("suggest.json") or {"suggestions": {}}
    done = store["suggestions"]
    items = []
    for i, t in enumerate(candidates(), 1):
        prompt = _prompt(t)
        prev = done.get(t.id)
        if prev and not prev.get("error") and prev.get("key") == _key(prompt):
            continue
        items.append((t.id, f"AI-{i:04d}", prompt))
    with ThreadPoolExecutor(max_workers=workers()) as pool:
        for tid, out in pool.map(_one, items):
            done[tid] = out
    store["suggestions"] = dict(sorted(done.items()))
    store["model"] = llm.model_name("suggest")
    store["backend"] = llm.backend()
    save("suggest.json", store)
    return {"called": len(items), "errors": sum(1 for v in done.values() if v.get("error")), "total": len(done)}
