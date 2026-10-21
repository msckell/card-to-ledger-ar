"""Runs the close and writes data/out/close.json plus the Excel workbook.

Receipt fields come from the AI reader when its committed output exists (data/ai/extract.json),
otherwise from the template parser. AI account suggestions and exception explanations are
read from their committed outputs too. Nothing here calls an LLM.
"""

from __future__ import annotations

import json
from decimal import Decimal

from pipeline import engine, exception_text, methodology
from pipeline.config import settings
from pipeline.engine import txn_dict
from pipeline.excel import write as write_excel
from pipeline.money import cents_str, to_cents
from pipeline.paths import AI_DIR, DATA, OUT
from pipeline.receipt_text import parse_all

EXCEL_NAME = "cierre_2026-09_andes_labs.xlsx"


def _load(name: str) -> dict | None:
    path = AI_DIR / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def receipt_fields(source: str) -> dict[str, dict]:
    if source == "template":
        return parse_all()
    data = _load("extract.json")
    if data is None:
        raise FileNotFoundError("data/ai/extract.json missing, run `ctl ai-extract` first")
    out = {}
    for rid, r in data["receipts"].items():
        if r.get("error"):
            out[rid] = {"unreadable": True, "source": "ai"}
            continue
        out[rid] = {
            "vendor": r["vendor"],
            "date": r["date"],
            "amount_cents": to_cents(r["amount"]) if r.get("amount") else None,
            "currency": r["currency"],
            "source": "ai",
        }
    return out


def ai_suggestions() -> dict[str, dict] | None:
    data = _load("suggest.json")
    if not data:
        return None
    return {tid: s for tid, s in data["suggestions"].items() if not s.get("error")}


def threshold() -> Decimal | None:
    path = DATA / "eval.json"
    if not path.exists():
        return None
    rec = json.loads(path.read_text(encoding="utf-8"))["threshold"]["recommended"]
    return Decimal(rec) if rec is not None else None


def run(source: str | None = None) -> dict:
    if source is None:
        source = "ai" if (AI_DIR / "extract.json").exists() else "template"
    receipts = receipt_fields(source)
    suggestions = ai_suggestions()
    thr = threshold()
    result = engine.run(receipts, suggestions, thr)
    txns = [txn_dict(t) for t in result["txns"]]
    by_id = {t["id"]: t for t in txns}
    explanations = (_load("explain.json") or {}).get("explanations", {})

    for e in result["exceptions"]:
        e["title"] = exception_text.TITLES[e["type"]]
        e["next_step"] = exception_text.NEXT_STEP[e["type"]]
        e["facts"] = exception_text.facts(e, by_id, receipts, result["threshold"])
        key = f"{e.get('txn_id') or e.get('receipt_id')}:{e['type']}"
        ex = explanations.get(key)
        if ex and ex.get("accepted"):
            e["explanation"], e["explanation_source"] = ex["text"], "ai_verified"
        else:
            e["explanation"] = exception_text.template(e, by_id)
            e["explanation_source"] = "template"
        e["key"] = key

    summary = _summary(txns, result, source)
    close = {
        "summary": summary,
        "entry": result["entry"],
        "entry_totals": result["entry_totals"],
        "balances": result["balances"],
        "transactions": txns,
        "journal_lines": [vars(ln) | {"debe": cents_str(ln.debe), "haber": cents_str(ln.haber)}
                          for ln in result["lines"]],
        "exceptions": result["exceptions"],
        "receipts": {rid: {k: (cents_str(v) if k == "amount_cents" and v is not None else v)
                           for k, v in r.items()} for rid, r in receipts.items()},
        "methodology": methodology.items(),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "close.json").write_text(json.dumps(close, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_excel(close, OUT / EXCEL_NAME)
    return close


def _summary(txns: list[dict], result: dict, source: str) -> dict:
    s = settings()

    def total(types, field="amount", sign=None):
        out = 0
        for t in txns:
            if t["type"] in types:
                v = to_cents(t[field])
                out += -v if sign and t["type"] in sign else v
        return out

    card_net = total({"card_purchase", "card_fee", "card_refund"}, sign={"card_refund"})
    card_net_ars = total({"card_purchase", "card_fee", "card_refund"}, "ars", sign={"card_refund"})
    payouts = total({"usdc_payout"})
    payouts_ars = total({"usdc_payout"}, "ars")
    split = {"rules": 0, "ai": 0, "review": 0}
    for t in txns:
        split[t["resolved_by"]] += 1
    no_rule = sum(1 for t in txns if not t["rule_id"])
    by_type: dict[str, int] = {}
    for t in txns:
        by_type[t["type"]] = by_type.get(t["type"], 0) + 1
    return {
        "company": s["company"]["name"],
        "period": s["period"]["month"],
        "transactions": len(txns),
        "by_type": by_type,
        "receipts": len(result["receipts"]),
        "receipt_source": source,
        "totals": {
            "card_net_usd": cents_str(card_net),
            "card_net_ars": cents_str(card_net_ars),
            "payouts_usdc": cents_str(payouts),
            "payouts_ars": cents_str(payouts_ars),
            "spend_usd": cents_str(card_net + payouts),
            "spend_ars": cents_str(card_net_ars + payouts_ars),
            "topups_ars": cents_str(total({"ars_topup"})),
        },
        "split": split,
        "no_rule": no_rule,
        "exceptions": len(result["exceptions"]),
        "threshold": result["threshold"],
        "excel": EXCEL_NAME,
    }
