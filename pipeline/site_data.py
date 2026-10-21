"""Everything the page shows, in one JSON file: data/site/site.json.

The page hardcodes no number. It reads this file at build time. The memo is rendered from
docs/memo.template.md with values from the same data, and written to docs/memo.md.
"""

from __future__ import annotations

import re
import shutil
from decimal import Decimal

from pipeline import fx
from pipeline.config import account_name, settings
from pipeline.jsonio import write_json
from pipeline.money import fmt, to_cents
from pipeline.paths import DOCS, OUT, RECEIPTS, ROOT, SITE, SITE_DATA

PCT = Decimal("100")


def pct(ratio: str | None) -> str | None:
    if ratio is None:
        return None
    return f"{(Decimal(ratio) * PCT).quantize(Decimal('0.1'))}%"


def money(amount: str) -> str:
    return fmt(to_cents(amount))


def _queue(close: dict) -> list[dict]:
    txns = {t["id"]: t for t in close["transactions"]}
    out = []
    for e in close["exceptions"]:
        t = txns.get(e.get("txn_id") or "")
        rid = e.get("receipt_id") or (t["receipt_id"] if t else None)
        r = close["receipts"].get(rid) if rid else None
        item = {
            "id": e["id"],
            "type": e["type"],
            "title": e["title"],
            "next_step": e["next_step"],
            "facts": e["facts"],
            "explanation": e["explanation"],
            "explanation_source": e["explanation_source"],
            "status": "Pending review",
        }
        if t:
            item["txn"] = {
                "id": t["id"],
                "date": t["posted_at"],
                "type": t["type"],
                "descriptor": t["descriptor"],
                "amount": money(t["amount"]),
                "currency": t["currency"],
                "ars": money(t["ars"]),
                "rate": str(Decimal(t["rate"]).quantize(Decimal("0.01"))),
                "cardholder": t["export"].get("cardholder", ""),
                "memo": t["export"].get("memo", ""),
                "proposed_account": f"{t['account']} {account_name(t['account'])}" if t["account"] else None,
            }
            if t.get("ai"):
                item["ai"] = {
                    "id": t["ai"]["id"],
                    "account": f"{t['ai']['account']} {t['ai']['account_name']}",
                    "confidence": t["ai"]["confidence"],
                    "reason": t["ai"]["reason"],
                }
        if r:
            amount = r.get("amount_cents")
            item["receipt"] = {
                "id": rid,
                "vendor": r.get("vendor"),
                "date": r.get("date"),
                "amount": money(amount) if amount else None,
                "currency": r.get("currency"),
                "file": f"receipts/{rid}.pdf",
            }
        out.append(item)
    return out


def _decision_table(ev: dict) -> list[dict]:
    ai_ex = ev["extraction"]["ai"]
    tmpl = ev["extraction"]["template_parser"]
    thr = ev["threshold"]
    an = ev["anomalies"]
    planted = sum(v["planted"] for k, v in an.items() if isinstance(v, dict))
    caught = sum(v["caught_in_review"] for k, v in an.items() if isinstance(v, dict))
    rows = [
        {"step": "Convert each movement to ARS", "handled_by": "Rules",
         "why": "A fixed rate convention applied to cited rates. Arithmetic, not judgment.",
         "accuracy": "Exact by construction, covered by tests"},
        {"step": "Read receipts", "handled_by": "AI",
         "why": ("Receipts come in any layout and language. Code checks every amount the AI reads "
                 "against the charge."),
         "accuracy": (f"{pct(ai_ex['per_field']['all_fields']['accuracy'])} of receipts with all four fields right "
                      f"(the template parser, written for these four layouts, scores "
                      f"{pct(tmpl['per_field']['all_fields']['accuracy'])})"
                      if ai_ex else "not run")},
        {"step": "Match receipts to movements", "handled_by": "Rules",
         "why": "Amount, date window and merchant name. Ties are not guessed, they go to a person.",
         "accuracy": f"{pct(ev['receipt_matching']['accuracy'])} of pairs right"},
        {"step": "Flag duplicates, missing receipts, mismatches and refunds", "handled_by": "Rules",
         "why": "Each check is a precise condition that must behave the same every month.",
         "accuracy": f"{caught} of {planted} planted problems sent to review"},
        {"step": "Code known merchants", "handled_by": "Rules",
         "why": "A short rule list covers most spend and is easy to audit.",
         "accuracy": f"{pct(ev['accounts']['rules']['accuracy'])} right"},
    ]
    if ev["accounts"].get("ai"):
        rec = thr.get("recommended_row")
        rows.append({
            "step": "Code merchants no rule covers", "handled_by": "AI above the threshold, a person below",
            "why": "Long tail of merchants. A rule per merchant does not scale, a wrong guess must not post.",
            "accuracy": (f"{pct(ev['accounts']['ai']['accuracy'])} right overall, "
                         + (f"{pct(rec['accuracy'])} on the {rec['accepted']} accepted at {thr['recommended']}"
                            if rec else "none accepted automatically")),
        })
    if ev.get("explanations"):
        e = ev["explanations"]
        rows.append({
            "step": "Explain each exception", "handled_by": "AI with a verifier, template as fallback",
            "why": "Plain language helps the reviewer. Numbers come only from code.",
            "accuracy": (f"{e['accepted_first_try'] + e['accepted_after_retry']} of {e['exceptions']} "
                         "passed the verifier"),
        })
    rows.append({"step": "Approve and post", "handled_by": "A person",
                 "why": "The controller owns the close. Nothing posts as final without review.",
                 "accuracy": "Not automated"})
    return rows


def export(close: dict, ev: dict) -> dict:
    s = close["summary"]
    src = fx.source_record()
    thr = ev["threshold"]
    queue = _queue(close)
    thr_value = Decimal(s["threshold"]) if s["threshold"] else None
    confident_in_review = sum(
        1 for t in close["transactions"]
        if t.get("ai") and thr_value is not None and Decimal(t["ai"]["confidence"]) >= thr_value
        and t["resolved_by"] == "review"
    )
    site = {
        "meta": {
            "title": "Card to Ledger AR",
            "subtitle": "Independent prototype for Jeeves by Máximo Sckell",
            "company": s["company"],
            "period": s["period"],
            "period_label": "September 2026",
            "fx_downloaded": src["downloaded_at"][:10],
            "fx_source": settings()["fx"]["source_url"],
            "model_note": ev.get("llm_usage"),
        },
        "summary": {
            "transactions": s["transactions"],
            "by_type": s["by_type"],
            "receipts": s["receipts"],
            "spend_usd": money(s["totals"]["spend_usd"]),
            "spend_ars": money(s["totals"]["spend_ars"]),
            "card_net_usd": money(s["totals"]["card_net_usd"]),
            "payouts_usdc": money(s["totals"]["payouts_usdc"]),
            "split": s["split"],
            "exceptions": s["exceptions"],
            "threshold": s["threshold"],
            "ai_confident_but_in_review": confident_in_review,
            "closing_rate": str(Decimal(close["balances"]["closing_rate"]).quantize(Decimal("0.01"))),
        },
        "queue": queue,
        "journal": {
            "rows": [{**r, "debe": money(r["debe"]) if r["debe"] != "0.00" else "",
                      "haber": money(r["haber"]) if r["haber"] != "0.00" else ""} for r in close["entry"]],
            "totals": {"debe": money(close["entry_totals"]["debe"]),
                       "haber": money(close["entry_totals"]["haber"]),
                       "balanced": close["entry_totals"]["balanced"]},
            "lines": len(close["journal_lines"]),
            "excel": f"downloads/{s['excel']}",
            "balances": close["balances"],
        },
        "eval": {
            "extraction": {
                "template": {k: v["accuracy"] for k, v in ev["extraction"]["template_parser"]["per_field"].items()},
                "ai": {k: v["accuracy"] for k, v in ev["extraction"]["ai"]["per_field"].items()}
                if ev["extraction"]["ai"] else None,
                "receipts": ev["extraction"]["template_parser"]["per_field"]["all_fields"]["total"],
            },
            "matching": {k: ev["receipt_matching"][k] for k in ("correct", "total", "accuracy")},
            "rules": {k: ev["accounts"]["rules"][k] for k in ("correct", "total", "accuracy")},
            "ai_accounts": {k: ev["accounts"]["ai"][k] for k in ("correct", "total", "accuracy", "small_sample")}
            if ev["accounts"].get("ai") else None,
            "anomalies": {k: v for k, v in ev["anomalies"].items() if isinstance(v, dict)},
            "threshold": {"rows": thr["rows"], "recommended": thr["recommended"], "why": thr["why"],
                          "target": thr.get("target_accuracy"), "recommended_row": thr.get("recommended_row")},
            "explanations": ev.get("explanations"),
            "decision_table": _decision_table(ev),
            "llm_usage": ev.get("llm_usage"),
        },
        "methodology": close["methodology"],
    }
    _render_memo(site)
    _write(site)
    _copy_files(close, queue)
    return site


def _write(site: dict) -> None:
    """The source of truth is data/site/site.json. The page builds from a copy inside site/ so
    a host that builds only that folder still has it."""
    write_json(SITE_DATA / "site.json", site)
    write_json(SITE / "src" / "data" / "site.json", site)


def _copy_files(close: dict, queue: list[dict]) -> None:
    pub = SITE / "public"
    rec_dir = pub / "receipts"
    if rec_dir.exists():
        shutil.rmtree(rec_dir)
    rec_dir.mkdir(parents=True)
    for item in queue:
        if item.get("receipt"):
            rid = item["receipt"]["id"]
            shutil.copyfile(RECEIPTS / f"{rid}.pdf", rec_dir / f"{rid}.pdf")
    dl = pub / "downloads"
    dl.mkdir(parents=True, exist_ok=True)
    for old in dl.glob("*.xlsx"):
        old.unlink()
    name = close["summary"]["excel"]
    shutil.copyfile(OUT / name, dl / name)


def memo_values(site: dict) -> dict[str, str]:
    """Flat values the memo template may use as {{name}}. All of them come from site.json."""
    s, e = site["summary"], site["eval"]
    thr = e["threshold"]
    rec = thr.get("recommended_row") or {}
    an = e["anomalies"]
    vals = {
        "transactions": str(s["transactions"]),
        "receipts": str(s["receipts"]),
        "spend_usd": s["spend_usd"],
        "spend_ars": s["spend_ars"],
        "rules_count": str(s["split"]["rules"]),
        "ai_count": str(s["split"]["ai"]),
        "review_count": str(s["split"]["review"]),
        "rules_share": pct(str(Decimal(s["split"]["rules"]) / Decimal(s["transactions"]))),
        "review_share": pct(str(Decimal(s["split"]["review"]) / Decimal(s["transactions"]))),
        "exceptions": str(s["exceptions"]),
        "rules_accuracy": pct(e["rules"]["accuracy"]),
        "rules_errors": str(e["rules"]["total"] - e["rules"]["correct"]),
        "matching_accuracy": pct(e["matching"]["accuracy"]),
        "planted": str(sum(v["planted"] for v in an.values())),
        "caught": str(sum(v["caught_in_review"] for v in an.values())),
        "threshold": thr["recommended"] or "none",
        "threshold_target": pct(thr["target"]) if thr.get("target") else "",
        "threshold_accepted": str(rec.get("accepted", 0)),
        "threshold_accuracy": pct(rec.get("accuracy")) or "",
        "no_rule": str(e["ai_accounts"]["total"]) if e["ai_accounts"] else "0",
        "ai_accounts_accuracy": pct(e["ai_accounts"]["accuracy"]) if e["ai_accounts"] else "",
        "ai_extract_all": pct(e["extraction"]["ai"]["all_fields"]) if e["extraction"]["ai"] else "",
        "template_extract_all": pct(e["extraction"]["template"]["all_fields"]),
    }
    if e.get("explanations"):
        ex = e["explanations"]
        vals["explain_passed"] = str(ex["accepted_first_try"] + ex["accepted_after_retry"])
        vals["explain_total"] = str(ex["exceptions"])
        vals["explain_fallback"] = str(ex["fell_back_to_template"])
    return vals


def _fill(template_name: str, vals: dict[str, str]) -> str:
    text = (DOCS / template_name).read_text(encoding="utf-8")

    def sub(m):
        key = m.group(1)
        if key not in vals:
            raise KeyError(f"{template_name} uses unknown value {{{{{key}}}}}")
        return vals[key]

    return re.sub(r"\{\{(\w+)\}\}", sub, text)


def _render_memo(site: dict) -> None:
    """docs/memo.md and README.md are rendered from their templates with values from site.json."""
    vals = memo_values(site)
    memo = _fill("memo.template.md", vals)
    with (DOCS / "memo.md").open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(memo)
    site["memo"] = memo
    readme = _fill("README.template.md", vals)
    with (ROOT / "README.md").open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(readme)


