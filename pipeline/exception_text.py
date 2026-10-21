"""Deterministic text for exceptions.

`facts` carries every number and is rendered only here. `template` is the plain English
explanation used when the AI explanation fails verification. It cites IDs and has no figures.
"""

from __future__ import annotations

from pipeline.config import account_name
from pipeline.money import fmt, to_cents

TITLES = {
    "missing_receipt": "Missing receipt",
    "duplicate_suspected": "Possible duplicate charge",
    "amount_mismatch": "Receipt does not match the charge",
    "refund_original_not_found": "Refund without its original charge",
    "refund_partial_link": "Partial refund linked by merchant only",
    "ai_below_threshold": "AI suggestion below the threshold",
    "no_rule": "No rule covers this merchant",
    "receipt_unmatched": "Receipt with no transaction",
    "receipt_unreadable": "Receipt could not be read",
}

NEXT_STEP = {
    "missing_receipt": "Ask the cardholder for the receipt",
    "duplicate_suspected": "Confirm with the cardholder and dispute the charge",
    "amount_mismatch": "Ask for the final receipt or record the difference",
    "refund_original_not_found": "Find the original charge in last month's close",
    "refund_partial_link": "Confirm which charge it refunds",
    "ai_below_threshold": "Pick the account",
    "no_rule": "Pick the account and consider a new rule",
    "receipt_unmatched": "Find the transaction or discard the receipt",
    "receipt_unreadable": "Open the file and read it by hand",
}


def next_step(e: dict, txns: dict[str, dict]) -> str:
    t = txns.get(e.get("txn_id") or "")
    if e["type"] == "missing_receipt" and t and t["type"] == "usdc_payout":
        return "Ask the contractor for the invoice"
    return NEXT_STEP[e["type"]]


def _money(amount: str, currency: str) -> str:
    return f"{currency} {fmt(to_cents(amount))}"


def facts(e: dict, txns: dict[str, dict], receipts: dict[str, dict], threshold: str | None) -> str:
    t = txns.get(e.get("txn_id") or "")
    kind = e["type"]
    if kind in ("receipt_unmatched", "receipt_unreadable"):
        r = receipts[e["receipt_id"]]
        if kind == "receipt_unreadable":
            return f"{e['receipt_id']} · the reader returned no usable fields"
        amount = f"{r['currency']} {fmt(r['amount_cents'])}" if r.get("amount_cents") is not None else "no amount"
        return f"{e['receipt_id']} · {r.get('vendor') or 'unknown vendor'} · {r.get('date') or 'no date'} · {amount}"
    base = f"{t['id']} · {t['posted_at']} · {t['descriptor']} · {_money(t['amount'], t['currency'])}"
    if t.get("export", {}).get("cardholder"):
        base += f" · {t['export']['cardholder']}"
    if kind == "missing_receipt":
        return base + " · no receipt found in the matching window"
    if kind == "duplicate_suspected":
        o = txns[t["duplicate_of"]]
        return base + f" · same descriptor and amount as {o['id']} posted {o['posted_at']} · only one receipt"
    if kind == "amount_mismatch":
        r = receipts[t["receipt_id"]]
        shown = f"{r['currency']} {fmt(r['amount_cents'])}"
        out = base + f" · receipt {t['receipt_id']} shows {shown}"
        if r["currency"] == t["currency"]:
            out += f" · difference {t['currency']} {fmt(to_cents(t['amount']) - r['amount_cents'])}"
        else:
            out += " · different currency"
        return out
    if kind == "refund_original_not_found":
        return base + " · no charge with the same descriptor and a larger amount in this export"
    if kind == "refund_partial_link":
        o = txns[t["refund_of"]]
        return base + (f" · tentatively linked to {o['id']} posted {o['posted_at']} for "
                       f"{_money(o['amount'], o['currency'])} · amounts differ")
    if kind == "ai_below_threshold":
        ai = t["ai"]
        return base + (f" · AI suggests {ai['account']} {account_name(ai['account'])} with confidence "
                       f"{ai['confidence']} · threshold {threshold}")
    if kind == "no_rule":
        return base + " · no account rule matches the descriptor"
    return base


def template(e: dict, txns: dict[str, dict]) -> str:
    kind = e["type"]
    tid = e.get("txn_id")
    t = txns.get(tid or "")
    if kind == "missing_receipt":
        who = "the contractor sends the invoice" if t and t["type"] == "usdc_payout" else "the cardholder uploads one"
        return f"No receipt was found for [{tid}]. It stays in review until {who}."
    if kind == "duplicate_suspected":
        return (f"[{tid}] repeats the merchant and amount of [{t['duplicate_of']}] within a short window, "
                "and only one receipt exists. It looks like a double charge.")
    if kind == "amount_mismatch":
        return (f"The receipt [{t['receipt_id']}] matches [{tid}] by merchant and date, but its amount or "
                "currency is different from the charge. The difference needs an explanation before posting.")
    if kind == "refund_original_not_found":
        return (f"[{tid}] is a refund, but its original charge is not in this month's export. "
                "It probably belongs to an earlier period.")
    if kind == "refund_partial_link":
        return (f"[{tid}] is a partial refund. It was linked to [{t['refund_of']}] because the merchant "
                "matches, but the amounts differ, so the link needs a person to confirm it.")
    if kind == "ai_below_threshold":
        return (f"No rule covers the merchant of [{tid}]. The AI suggestion is not confident enough to "
                "be accepted automatically.")
    if kind == "no_rule":
        return f"No rule covers the merchant of [{tid}]."
    if kind == "receipt_unmatched":
        return f"The receipt [{e['receipt_id']}] did not match any transaction in the export."
    if kind == "receipt_unreadable":
        return f"The receipt [{e['receipt_id']}] could not be read."
    return ""
