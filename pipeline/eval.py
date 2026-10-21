"""Measures every step of the close against the generator's ground truth. Writes data/eval.json.

Small samples are marked. Nothing here claims more than the counts show.
"""

from __future__ import annotations

import json
from decimal import Decimal

from pipeline.config import settings
from pipeline.engine import _tokens
from pipeline.paths import AI_DIR, DATA, TRUTH
from pipeline.receipt_text import parse_all

PLANTED_TO_FOUND = {
    "missing_receipt": "missing_receipt",
    "duplicate": "duplicate_suspected",
    "amount_mismatch": "amount_mismatch",
    "refund_original_not_in_period": "refund_original_not_found",
}
SMALL_SAMPLE = 20


def truth() -> dict:
    return json.loads((TRUTH / "ground_truth.json").read_text(encoding="utf-8"))


def _ratio(hits: int, n: int) -> dict:
    return {
        "correct": hits,
        "total": n,
        "accuracy": str((Decimal(hits) / Decimal(n)).quantize(Decimal("0.001"))) if n else None,
        "small_sample": n < SMALL_SAMPLE,
    }


def _vendor_ok(got: str | None, want: str) -> bool:
    if not got:
        return False
    a, b = _tokens(got), _tokens(want)
    return bool(a) and bool(b) and (a == b or a <= b or b <= a)


def extraction_accuracy(fields: dict[str, dict], gt: dict) -> dict:
    n = 0
    hits = {"vendor": 0, "date": 0, "amount": 0, "currency": 0, "all_fields": 0}
    errors = []
    for rid, want in gt["receipts"].items():
        got = fields.get(rid)
        n += 1
        if not got or got.get("unreadable"):
            errors.append({"receipt_id": rid, "fields": ["unreadable"]})
            continue
        amount = got.get("amount_cents")
        ok = {
            "vendor": _vendor_ok(got.get("vendor"), want["vendor"]),
            "date": got.get("date") == want["date"],
            "amount": amount is not None and amount == int(Decimal(want["amount"]) * 100),
            "currency": got.get("currency") == want["currency"],
        }
        for k, v in ok.items():
            hits[k] += int(v)
        if all(ok.values()):
            hits["all_fields"] += 1
        else:
            errors.append({"receipt_id": rid, "layout": want["layout"],
                           "fields": [k for k, v in ok.items() if not v]})
    by_layout: dict[str, list[int]] = {}
    for rid, want in gt["receipts"].items():
        bucket = by_layout.setdefault(want["layout"], [0, 0])
        bucket[1] += 1
        if not any(e["receipt_id"] == rid for e in errors):
            bucket[0] += 1
    return {
        "per_field": {k: _ratio(v, n) for k, v in hits.items()},
        "by_layout": {k: _ratio(h, t) for k, (h, t) in sorted(by_layout.items())},
        "errors": errors,
    }


def anomaly_detection(close: dict, gt: dict) -> dict:
    found: dict[str, set[str]] = {}
    for e in close["exceptions"]:
        if e.get("txn_id"):
            found.setdefault(e["type"], set()).add(e["txn_id"])
    txt = {t["id"]: t for t in close["transactions"]}
    out = {}
    for planted_type, found_type in PLANTED_TO_FOUND.items():
        planted = {tid for tid, tr in gt["transactions"].items() if planted_type in tr["anomalies"]}
        got = found.get(found_type, set())
        if planted_type == "duplicate":
            # A pair counts once: flagging either side of a planted duplicate is a hit.
            pairs = {tid: {tid, gt["transactions"][tid]["duplicate_of"]} for tid in planted}
            tp = sum(1 for tid in planted if pairs[tid] & got)
            fp = sum(1 for g in got if not any(g in p for p in pairs.values()))
        else:
            tp = len(planted & got)
            fp = len(got - planted)
        caught = sum(1 for tid in planted if txt[tid]["resolved_by"] == "review")
        out[planted_type] = {
            "planted": len(planted),
            "caught_in_review": caught,
            "found": len(got),
            "true_positives": tp,
            "false_positives": fp,
            "missed": len(planted) - tp,
            "missed_ids": sorted(planted - got) if planted_type != "duplicate" else [],
            "false_positive_ids": sorted(got - planted) if planted_type != "duplicate" else [],
        }
    legit = [tid for tid, tr in gt["transactions"].items() if tr.get("legit_repeat_of")]
    out["legit_repeat_not_flagged"] = all(
        "duplicate_suspected" not in txt[tid]["exceptions"]
        and "duplicate_suspected" not in txt[gt["transactions"][tid]["legit_repeat_of"]]["exceptions"]
        for tid in legit
    )
    return out


def receipt_matching(close: dict, gt: dict) -> dict:
    hits = n = 0
    wrong = []
    rc = gt["receipts"]
    for t in close["transactions"]:
        want = gt["transactions"][t["id"]]["receipt_id"]
        if want is None and t["receipt_id"] is None:
            continue
        n += 1
        got = t["receipt_id"]
        same = got == want or (
            got and want and all(rc[got][k] == rc[want][k] for k in ("vendor", "date", "amount", "currency"))
        )
        hits += int(bool(same))
        if not same:
            wrong.append({"txn_id": t["id"], "expected": want, "got": got})
    return {**_ratio(hits, n), "wrong": wrong}


def account_accuracy(close: dict, gt: dict) -> dict:
    rules_hits = rules_n = 0
    rule_errors = []
    for t in close["transactions"]:
        tr = gt["transactions"][t["id"]]
        if not t["rule_id"] or t["type"] in ("card_refund",) or "duplicate" in tr["anomalies"]:
            continue
        rules_n += 1
        if t["account"] == tr["account"]:
            rules_hits += 1
        else:
            rule_errors.append({"txn_id": t["id"], "rule_id": t["rule_id"], "descriptor": t["descriptor"],
                                "got": t["account"], "expected": tr["account"]})
    out = {"rules": {**_ratio(rules_hits, rules_n), "errors": rule_errors}}
    sugg = _ai_suggestions()
    if sugg:
        ai_hits = ai_n = 0
        ai_errors = []
        for tid, s in sugg.items():
            tr = gt["transactions"][tid]
            ai_n += 1
            if s["account"] == tr["account"]:
                ai_hits += 1
            else:
                ai_errors.append({"txn_id": tid, "got": s["account"], "expected": tr["account"],
                                  "confidence": s["confidence"]})
        out["ai"] = {**_ratio(ai_hits, ai_n), "errors": ai_errors}
    return out


def _ai_suggestions() -> dict | None:
    path = AI_DIR / "suggest.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: v for k, v in data["suggestions"].items() if not v.get("error")}


def threshold_sweep(gt: dict) -> dict | None:
    sugg = _ai_suggestions()
    if not sugg:
        return None
    cfg = settings()["ai"]
    target = Decimal(cfg["target_accuracy"])
    min_n = cfg["min_accepted_for_threshold"]
    rows = []
    n = len(sugg)
    for th in cfg["thresholds"]:
        t = Decimal(th)
        accepted = [(tid, s) for tid, s in sugg.items() if Decimal(s["confidence"]) >= t]
        hits = sum(1 for tid, s in accepted if s["account"] == gt["transactions"][tid]["account"])
        rows.append({
            "threshold": th,
            "accepted": len(accepted),
            "share_auto_accepted": str((Decimal(len(accepted)) / Decimal(n)).quantize(Decimal("0.001"))),
            "accuracy": str((Decimal(hits) / Decimal(len(accepted))).quantize(Decimal("0.001")))
            if accepted else None,
            "errors_accepted": len(accepted) - hits,
        })
    recommended = None
    for r in rows:
        if r["accuracy"] is not None and Decimal(r["accuracy"]) >= target and r["accepted"] >= min_n:
            recommended = r["threshold"]
            break
    if recommended:
        r = next(x for x in rows if x["threshold"] == recommended)
        why = (f"Lowest threshold whose auto accepted suggestions reach the target accuracy of "
               f"{target} with at least {min_n} accepted. Picked on this month's labeled synthetic "
               "data. In production it should be picked on a held out labeled sample and rechecked "
               "every month.")
    else:
        r = None
        why = (f"No threshold reaches the target accuracy of {target} with at least {min_n} accepted, "
               "so every AI suggestion goes to a person.")
    return {"target_accuracy": str(target), "suggestions": n, "rows": rows,
            "recommended": recommended, "recommended_row": r, "why": why}


def explanation_stats() -> dict | None:
    path = AI_DIR / "explain.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    ex = data["explanations"].values()
    first_try = sum(1 for e in ex if e["accepted"] and e["attempts"] == 1)
    retried = sum(1 for e in ex if e["accepted"] and e["attempts"] > 1)
    fallback = sum(1 for e in ex if not e["accepted"])
    reasons: dict[str, int] = {}
    for e in ex:
        for a in e["log"]:
            for r in a.get("violations", []):
                key = r.split(":")[0]
                reasons[key] = reasons.get(key, 0) + 1
    total = len(data["explanations"])
    return {
        "exceptions": total,
        "accepted_first_try": first_try,
        "accepted_after_retry": retried,
        "fell_back_to_template": fallback,
        "pass_rate": _ratio(first_try + retried, total),
        "rejections_by_reason": reasons,
    }


def run(close: dict, write: bool = True) -> dict:
    gt = truth()
    template = extraction_accuracy(parse_all(), gt)
    ai_extract = None
    path = AI_DIR / "extract.json"
    if path.exists():
        from pipeline.close import receipt_fields

        ai_extract = extraction_accuracy(receipt_fields("ai"), gt)
    result = {
        "note": "Measured against the generator's ground truth. Synthetic data, one month.",
        "transactions": len(close["transactions"]),
        "extraction": {"template_parser": template, "ai": ai_extract},
        "receipt_matching": receipt_matching(close, gt),
        "anomalies": anomaly_detection(close, gt),
        "accounts": account_accuracy(close, gt),
        "threshold": threshold_sweep(gt) or {"recommended": None, "rows": [], "why": "AI not run yet"},
        "explanations": explanation_stats(),
        "split": close["summary"]["split"],
        "llm_usage": _llm_usage(),
    }
    if write:
        (DATA / "eval.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                                        encoding="utf-8")
    return result


def _llm_usage() -> dict | None:
    path = AI_DIR / "usage.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
