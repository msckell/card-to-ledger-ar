"""AI use 3: one plain English explanation per exception.

The model sees the deterministic facts of the exception and writes one or two sentences that
cite IDs in square brackets and contain no figures. The verifier rejects figures, invented IDs
and claims like "approved". On rejection the model gets the reasons and tries again, up to two
more times. After that the template text is used. Every attempt is logged.
"""

from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel, Field

from pipeline.ai import llm, verifier
from pipeline.ai.store import load, save, workers
from pipeline.jsonio import read_json
from pipeline.paths import OUT

MAX_ATTEMPTS = 3

SYSTEM = """You write short notes for an accountant who reviews exceptions in a month end close.

For the exception you are given, write one or two plain English sentences: what looks wrong and \
what the reviewer should check. Write for a busy controller, no jargon.

Hard rules:
- Cite the transactions and receipts by their IDs in square brackets, for example [TX-0042] or \
[RC-0107]. Use only the IDs listed as allowed.
- Do not write any number, amount, date, percentage or currency symbol, not even in words. The \
numbers are shown to the reader next to your note.
- Do not say that anything is approved, verified, compliant, reconciled or fraudulent. You only \
describe what the reviewer should look at.
- At most two sentences."""


KIND_LABEL = {
    "card_purchase": "this card charge",
    "card_refund": "this card refund",
    "card_fee": "this card fee",
    "usdc_payout": "this USDC payout to a contractor",
    "ars_topup": "this ARS top up",
    "card_settlement": "this card statement payment",
}


class Note(BaseModel):
    text: str = Field(max_length=600)


def _allowed(e: dict, t: dict | None) -> dict[str, str]:
    """IDs the note may cite, each with what it is. Rule IDs are not evidence, so they are left out."""
    ids: dict[str, str] = {}
    if t:
        ids[t["id"]] = KIND_LABEL.get(t["type"], "this movement")
        if t.get("receipt_id"):
            ids[t["receipt_id"]] = "the receipt matched to it"
        if t.get("duplicate_of"):
            ids[t["duplicate_of"]] = "the earlier charge it repeats"
        if t.get("refund_of"):
            ids[t["refund_of"]] = "the charge it was tentatively linked to"
        if t.get("ai"):
            ids[t["ai"]["id"]] = "the AI account suggestion"
    if e.get("receipt_id"):
        ids[e["receipt_id"]] = "this receipt"
    return ids


def _prompt(e: dict, t: dict | None, allowed: dict[str, str]) -> str:
    lines = [
        f"Exception type: {e['title']}",
        f"Movement: {KIND_LABEL.get(t['type'], 'none') if t else 'none, this is a receipt with no movement'}",
        f"Facts: {e['facts']}",
        f"Suggested next step: {e['next_step']}",
    ]
    if t:
        if t["export"].get("memo"):
            lines.append(f"Cardholder memo: {t['export']['memo']}")
        if t.get("ai"):
            lines.append(f"AI account suggestion {t['ai']['id']}: {t['ai']['account_name']}. "
                         f"Reason given: {t['ai']['reason']}")
    lines.append("IDs you may cite: " + "; ".join(f"{k} ({v})" for k, v in sorted(allowed.items())))
    return "\n".join(lines)


def _key(prompt: str) -> str:
    return hashlib.sha256((SYSTEM + llm.model_name("explain") + prompt).encode()).hexdigest()[:16]


def _one(item: tuple[str, str, dict[str, str]]) -> tuple[str, dict]:
    key, prompt, allowed_map = item
    allowed = set(allowed_map)
    log = []
    current = prompt
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            reply = llm.ask("explain", SYSTEM, current, Note, 1500)
        except llm.LlmError as exc:
            llm.failed_call("explain")
            log.append({"attempt": attempt, "error": str(exc)})
            continue
        text = reply.data.text.strip()
        violations = verifier.check(text, allowed)
        log.append({"attempt": attempt, "text": text, "violations": violations})
        if not violations:
            return key, {"accepted": True, "text": text, "attempts": attempt, "log": log,
                         "key": _key(prompt), "model": reply.model}
        current = (prompt + "\n\nYour previous note was rejected by the verifier for these reasons:\n- "
                   + "\n- ".join(violations) + f"\nPrevious note: {text}\nWrite a new note that follows every rule.")
    return key, {"accepted": False, "text": None, "attempts": len(log), "log": log, "key": _key(prompt)}


def run() -> dict:
    close = read_json(OUT / "close.json")
    txns = {t["id"]: t for t in close["transactions"]}
    store = load("explain.json") or {"explanations": {}}
    done = store["explanations"]
    items = []
    keys_now = set()
    for e in close["exceptions"]:
        t = txns.get(e.get("txn_id") or "")
        allowed = _allowed(e, t)
        prompt = _prompt(e, t, allowed)
        keys_now.add(e["key"])
        prev = done.get(e["key"])
        if prev and prev.get("key") == _key(prompt) and (prev["accepted"] or prev["attempts"] >= MAX_ATTEMPTS):
            continue
        items.append((e["key"], prompt, allowed))
    with ThreadPoolExecutor(max_workers=workers()) as pool:
        for key, out in pool.map(_one, items):
            done[key] = out
    # Exceptions that no longer exist in the close are dropped from the store.
    store["explanations"] = {k: v for k, v in sorted(done.items()) if k in keys_now}
    store["model"] = llm.model_name("explain")
    store["backend"] = llm.backend()
    save("explain.json", store)
    ex = store["explanations"].values()
    return {"called": len(items), "accepted": sum(1 for v in ex if v["accepted"]),
            "fallback_to_template": sum(1 for v in ex if not v["accepted"]), "total": len(ex)}
