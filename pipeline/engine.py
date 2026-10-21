"""Deterministic close engine.

Order: account rules, receipt matching, checks (duplicates, missing receipts, amount
mismatches, refunds), AI suggestions for what no rule covers (accepted only above a
threshold), resolution, journal entry in ARS with month end remeasurement, balance check.

The engine never reads the ground truth.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from pipeline import fx
from pipeline.config import account_name, chart, rules, settings
from pipeline.money import cents_str, convert, to_cents
from pipeline.paths import RAW

RECEIPT_REQUIRED = {"card_purchase", "usdc_payout"}
SUSPENSE = "1.1.09"
USDC_ACCOUNT = "1.1.02"
CARD_PAYABLE = "2.1.01"
BANK_ARS = "1.1.01"
FX_RESULT = "5.2.01"

STOP = {"inc", "llc", "ltd", "the", "com", "bv", "b", "v", "sarl", "pbc", "co", "company", "www",
        "store", "sq", "tst", "paypal", "paddle", "net", "lemsqzy", "dd", "sp", "mktp", "us",
        "pty", "limited", "unlimited", "group", "services", "llc."}


class BalanceError(Exception):
    pass


@dataclass
class Txn:
    id: str
    posted_at: date
    type: str
    descriptor: str
    amount_cents: int
    currency: str
    cardholder: str = ""
    memo: str = ""
    raw: dict = field(default_factory=dict)
    rule_id: str | None = None
    rule_account: str | None = None
    receipt_id: str | None = None
    receipt_match: str | None = None  # exact | amount_differs
    exceptions: list[str] = field(default_factory=list)
    duplicate_of: str | None = None
    refund_of: str | None = None
    ai: dict | None = None
    resolved_by: str = ""  # rules | ai | review
    account: str = ""  # account proposed for the line (rule, AI or original)
    posted_account: str = ""  # account the journal uses (suspense when in review)
    status: str = ""
    rate: Decimal | None = None
    ars_cents: int = 0


def load_export() -> list[Txn]:
    data = json.loads((RAW / "transactions.json").read_text(encoding="utf-8"))
    out = []
    for row in data["transactions"]:
        out.append(
            Txn(
                id=row["id"],
                posted_at=date.fromisoformat(row["posted_at"]),
                type=row["type"],
                descriptor=row["descriptor"],
                amount_cents=to_cents(row["amount"]),
                currency=row["currency"],
                cardholder=row.get("cardholder", ""),
                memo=row.get("memo", ""),
                raw=row,
            )
        )
    return out


# ---------- rules ----------

def apply_rules(txns: list[Txn]) -> None:
    cfg = rules()
    by_type = {r["type"]: r for r in cfg["type_rules"]}
    compiled = [(r, re.compile(r["pattern"], re.IGNORECASE)) for r in cfg["descriptor_rules"]]
    for t in txns:
        if t.type in by_type:
            r = by_type[t.type]
            t.rule_id = r["id"]
            t.rule_account = None if r["account"] == "original" else r["account"]
            continue
        for r, rx in compiled:
            if rx.search(t.descriptor):
                t.rule_id = r["id"]
                t.rule_account = r["account"]
                break


def _rule(rule_id: str | None) -> dict | None:
    if not rule_id:
        return None
    for r in rules()["descriptor_rules"]:
        if r["id"] == rule_id:
            return r
    return None


def receipt_required(t: Txn) -> bool:
    if t.type not in RECEIPT_REQUIRED:
        return False
    r = _rule(t.rule_id)
    return not (r and r.get("receipt_exempt"))


# ---------- receipt matching ----------

def _tokens(s: str) -> set[str]:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = s.replace("'", "")
    toks = re.findall(r"[a-z]+", s)
    return {t for t in toks if len(t) >= 3 and t not in STOP}


def _same_token(a: str, b: str) -> bool:
    return a == b or (len(a) >= 3 and len(b) >= 3 and (a.startswith(b) or b.startswith(a)))


def merchant_similarity(t: Txn, vendor: str | None) -> Decimal:
    if not vendor:
        return Decimal(0)
    left = _tokens(t.raw.get("counterparty") or t.descriptor)
    right = _tokens(vendor)
    r = _rule(t.rule_id)
    vendors = r.get("vendors", []) if r else []
    for alias in vendors:
        if _tokens(alias) != right:
            continue
        # The rule translates a card descriptor into the legal name on the receipt. When a rule
        # groups several brands, the alias must also share a word with this descriptor.
        if len(vendors) == 1 or any(_same_token(a, b) for a in left for b in _tokens(alias)):
            return Decimal(1)
    if not left or not right:
        return Decimal(0)
    hits = sum(1 for a in left if any(_same_token(a, b) for b in right))
    return (Decimal(hits) / Decimal(min(len(left), len(right)))).quantize(Decimal("0.01"))


def match_receipts(txns: list[Txn], receipts: dict[str, dict]) -> dict[str, str]:
    """One to one assignment of receipts to transactions. Returns receipt_id -> txn_id."""
    m = settings()["matching"]
    before = timedelta(days=m["date_window_before"])
    after = timedelta(days=m["date_window_after"])
    tol = m["amount_tolerance_cents"]
    min_sim = Decimal(m["merchant_similarity_min"])
    pairs = []
    for rid, r in receipts.items():
        if r.get("unreadable") or not r.get("date"):
            continue
        rdate = date.fromisoformat(r["date"])
        for t in txns:
            if not receipt_required(t):
                continue
            if not (t.posted_at - before <= rdate <= t.posted_at + after):
                continue
            sim = merchant_similarity(t, r.get("vendor"))
            same_amount = (
                r.get("amount_cents") is not None
                and r.get("currency") == t.currency
                and abs(r["amount_cents"] - t.amount_cents) <= tol
            )
            if same_amount:
                score = Decimal(10) + sim * 5
                kind = "exact"
            elif sim >= min_sim:
                score = Decimal(5) + sim * 5
                kind = "amount_differs"
            else:
                continue
            gap = abs((t.posted_at - rdate).days)
            pairs.append((-score, gap, rid, t.id, kind))
    pairs.sort()
    used_r, used_t, out = set(), set(), {}
    by_id = {t.id: t for t in txns}

    def assign(rid, tid, kind):
        used_r.add(rid)
        used_t.add(tid)
        out[rid] = tid
        by_id[tid].receipt_id = rid
        by_id[tid].receipt_match = kind

    # Pass 1: receipts whose amount and currency equal the charge.
    for _neg, _gap, rid, tid, kind in pairs:
        if kind == "exact" and rid not in used_r and tid not in used_t:
            assign(rid, tid, kind)
    # Pass 2: receipts that pair by merchant and date only. When two open transactions tie on
    # score, the receipt is not guessed. It stays unmatched and goes to a person.
    open_pairs = [p for p in pairs if p[4] == "amount_differs" and p[2] not in used_r and p[3] not in used_t]
    by_receipt: dict[str, list] = defaultdict(list)
    for p in open_pairs:
        by_receipt[p[2]].append(p)
    ambiguous = {rid for rid, c in by_receipt.items() if len(c) > 1 and c[0][0] == c[1][0]}
    for _neg, _gap, rid, tid, kind in open_pairs:
        if rid not in used_r and tid not in used_t and rid not in ambiguous:
            assign(rid, tid, kind)
    return out


# ---------- checks ----------

def _desc_key(desc: str) -> str:
    return re.sub(r"\s+", " ", desc.strip().upper())


def detect_duplicates(txns: list[Txn]) -> None:
    window = settings()["matching"]["duplicate_window_days"]
    groups: dict[tuple, list[Txn]] = defaultdict(list)
    for t in txns:
        if t.type == "card_purchase":
            groups[(_desc_key(t.descriptor), t.amount_cents)].append(t)
    for members in groups.values():
        if len(members) < 2:
            continue
        members.sort(key=lambda t: (t.posted_at, t.id))
        for i, t in enumerate(members):
            if t.receipt_id:
                continue
            twins = [o for o in members[:i] + members[i + 1:]
                     if abs((o.posted_at - t.posted_at).days) <= window]
            if not twins:
                continue
            anchor = next((o for o in twins if o.receipt_id), None)
            earlier = [o for o in twins if o.posted_at <= t.posted_at and o.id < t.id]
            if anchor or earlier:
                t.duplicate_of = (anchor or earlier[0]).id
                t.exceptions.append("duplicate_suspected")


def detect_missing_receipts(txns: list[Txn]) -> None:
    for t in txns:
        if receipt_required(t) and not t.receipt_id and "duplicate_suspected" not in t.exceptions:
            t.exceptions.append("missing_receipt")


def detect_amount_mismatches(txns: list[Txn]) -> None:
    for t in txns:
        if t.receipt_match == "amount_differs":
            t.exceptions.append("amount_mismatch")


def link_refunds(txns: list[Txn]) -> None:
    lookback = settings()["matching"]["refund_lookback_days"]
    purchases = [t for t in txns if t.type == "card_purchase"]
    for t in txns:
        if t.type != "card_refund":
            continue
        cands = [
            p for p in purchases
            if _desc_key(p.descriptor) == _desc_key(t.descriptor)
            and p.amount_cents >= t.amount_cents
            and t.posted_at - timedelta(days=lookback) <= p.posted_at <= t.posted_at
            and "duplicate_suspected" not in p.exceptions
        ]
        if cands:
            exact = [p for p in cands if p.amount_cents == t.amount_cents]
            pick = exact or cands
            t.refund_of = max(pick, key=lambda p: (p.posted_at, p.id)).id
            if not exact:
                # Linked by merchant only. The original could be in an earlier month.
                t.exceptions.append("refund_partial_link")
        else:
            t.exceptions.append("refund_original_not_found")


# ---------- resolution ----------

def resolve(txns: list[Txn], ai: dict[str, dict] | None, threshold: Decimal | None) -> None:
    by_id = {t.id: t for t in txns}
    for t in txns:
        if t.type == "card_refund":
            continue
        if t.rule_account:
            t.account = t.rule_account
        elif ai and t.id in ai:
            t.ai = ai[t.id]
            t.account = t.ai["account"]
            if threshold is None or Decimal(t.ai["confidence"]) < threshold:
                t.exceptions.append("ai_below_threshold")
        else:
            t.exceptions.append("no_rule")
        if t.exceptions:
            t.resolved_by, t.status = "review", "pending review"
        elif t.rule_account:
            t.resolved_by, t.status = "rules", "posted"
        else:
            t.resolved_by, t.status = "ai", "posted"
        t.posted_account = t.account if t.resolved_by != "review" else SUSPENSE
    for t in txns:
        if t.type != "card_refund":
            continue
        orig = by_id.get(t.refund_of) if t.refund_of else None
        if orig:
            t.account = orig.account
            t.posted_account = orig.posted_account
            if orig.resolved_by == "review":
                t.exceptions.append("original_in_review")
        t.resolved_by = "review" if t.exceptions else "rules"
        t.status = "pending review" if t.exceptions else "posted"
        if t.resolved_by == "review":
            t.posted_account = SUSPENSE


# ---------- journal ----------

@dataclass
class Line:
    id: str
    txn_id: str
    date: str
    account: str
    debe: int
    haber: int
    basis: str
    status: str
    approved_by: str
    detail: str


def _approval(t: Txn) -> tuple[str, str]:
    if t.resolved_by == "rules":
        return f"rule {t.rule_id}", "rules engine (deterministic)"
    if t.resolved_by == "ai":
        return f"AI suggestion {t.ai['id']}", "auto accepted: AI confidence at or above threshold"
    return "suspense until reviewed", "pending review"


def build_journal(txns: list[Txn]) -> tuple[list[Line], dict]:
    lines: list[Line] = []
    usdc_per_usd = Decimal(settings()["fx"]["usdc_per_usd"])

    def add(t_id, d, account, debe, haber, basis, status, approved, detail):
        lines.append(Line(f"JL-{len(lines) + 1:04d}", t_id, d, account, debe, haber, basis, status,
                          approved, detail))

    for t in txns:
        t.rate = fx.rate(t.posted_at)
        d = t.posted_at.isoformat()
        basis, approved = _approval(t)
        if t.type in ("card_purchase", "card_fee"):
            ars = convert(t.amount_cents, t.rate)
            t.ars_cents = ars
            add(t.id, d, t.posted_account, ars, 0, basis, t.status, approved, t.descriptor)
            add(t.id, d, CARD_PAYABLE, 0, ars, basis, t.status, approved, t.descriptor)
        elif t.type == "card_refund":
            ars = convert(t.amount_cents, t.rate)
            t.ars_cents = ars
            basis = f"refund of {t.refund_of}" if t.refund_of else basis
            add(t.id, d, CARD_PAYABLE, ars, 0, basis, t.status, approved, t.descriptor)
            add(t.id, d, t.posted_account, 0, ars, basis, t.status, approved, t.descriptor)
        elif t.type == "usdc_payout":
            ars = convert(t.amount_cents, t.rate * usdc_per_usd)
            t.ars_cents = ars
            add(t.id, d, t.posted_account, ars, 0, basis, t.status, approved, t.descriptor)
            add(t.id, d, USDC_ACCOUNT, 0, ars, basis, t.status, approved, t.descriptor)
        elif t.type == "card_settlement":
            ars = convert(t.amount_cents, t.rate * usdc_per_usd)
            t.ars_cents = ars
            add(t.id, d, CARD_PAYABLE, ars, 0, basis, t.status, approved, t.descriptor)
            add(t.id, d, USDC_ACCOUNT, 0, ars, basis, t.status, approved, t.descriptor)
        elif t.type == "ars_topup":
            usdc = to_cents(t.raw["credited_amount"])
            book = convert(usdc, t.rate * usdc_per_usd)
            t.ars_cents = t.amount_cents
            add(t.id, d, USDC_ACCOUNT, book, 0, basis, t.status, approved,
                "USDC received, valued at the official rate")
            add(t.id, d, BANK_ARS, 0, t.amount_cents, basis, t.status, approved, "ARS sent from the bank")
            diff = t.amount_cents - book
            if diff > 0:
                add(t.id, d, FX_RESULT, diff, 0, basis, t.status, approved,
                    "Cost of buying USDC above the official rate")
            elif diff < 0:
                add(t.id, d, FX_RESULT, 0, -diff, basis, t.status, approved,
                    "USDC bought below the official rate")
        else:
            raise ValueError(f"unknown type {t.type}")

    balances = _remeasure(txns, lines, add)
    return lines, balances


def _remeasure(txns: list[Txn], lines: list[Line], add) -> dict:
    s = settings()
    end = date.fromisoformat(s["period"]["end"])
    opening_day = date.fromisoformat(s["opening_balances"]["as_of"])
    usdc_per_usd = Decimal(s["fx"]["usdc_per_usd"])
    close_rate = fx.rate(end)
    open_rate = fx.rate(opening_day)
    usdc_open = to_cents(s["opening_balances"]["usdc"])
    card_open = to_cents(s["opening_balances"]["card_payable_usd"])

    usdc_bal, card_bal = usdc_open, card_open
    for t in txns:
        if t.type == "ars_topup":
            usdc_bal += to_cents(t.raw["credited_amount"])
        elif t.type == "usdc_payout":
            usdc_bal -= t.amount_cents
        elif t.type == "card_settlement":
            usdc_bal -= t.amount_cents
            card_bal -= t.amount_cents
        elif t.type in ("card_purchase", "card_fee"):
            card_bal += t.amount_cents
        elif t.type == "card_refund":
            card_bal -= t.amount_cents

    def book(account: str) -> int:
        return sum(ln.debe - ln.haber for ln in lines if ln.account == account)

    usdc_open_ars = convert(usdc_open, open_rate * usdc_per_usd)
    card_open_ars = convert(card_open, open_rate)
    usdc_book = usdc_open_ars + book(USDC_ACCOUNT)
    card_book = card_open_ars - book(CARD_PAYABLE)  # credit balance as a positive number
    usdc_target = convert(usdc_bal, close_rate * usdc_per_usd)
    card_target = convert(card_bal, close_rate)
    d = end.isoformat()
    basis, approved = "month end remeasurement", "rules engine (deterministic)"

    diff = usdc_target - usdc_book
    if diff > 0:
        add("REMEASURE", d, USDC_ACCOUNT, diff, 0, basis, "posted", approved, "Cuenta USDC at the closing rate")
        add("REMEASURE", d, FX_RESULT, 0, diff, basis, "posted", approved, "Gain on the USDC balance")
    elif diff < 0:
        add("REMEASURE", d, FX_RESULT, -diff, 0, basis, "posted", approved, "Loss on the USDC balance")
        add("REMEASURE", d, USDC_ACCOUNT, 0, -diff, basis, "posted", approved, "Cuenta USDC at the closing rate")
    diff_card = card_target - card_book
    if diff_card > 0:
        add("REMEASURE", d, FX_RESULT, diff_card, 0, basis, "posted", approved, "Loss on the card balance")
        add("REMEASURE", d, CARD_PAYABLE, 0, diff_card, basis, "posted", approved,
            "Tarjeta corporativa a pagar at the closing rate")
    elif diff_card < 0:
        add("REMEASURE", d, CARD_PAYABLE, -diff_card, 0, basis, "posted", approved,
            "Tarjeta corporativa a pagar at the closing rate")
        add("REMEASURE", d, FX_RESULT, 0, -diff_card, basis, "posted", approved, "Gain on the card balance")

    return {
        "opening_rate": str(open_rate),
        "closing_rate": str(close_rate),
        "usdc": {"opening_usd": cents_str(usdc_open), "closing_usd": cents_str(usdc_bal),
                 "opening_ars": cents_str(usdc_open_ars), "book_before_ars": cents_str(usdc_book),
                 "closing_ars": cents_str(usdc_target), "remeasurement_ars": cents_str(diff)},
        "card_payable": {"opening_usd": cents_str(card_open), "closing_usd": cents_str(card_bal),
                         "opening_ars": cents_str(card_open_ars), "book_before_ars": cents_str(card_book),
                         "closing_ars": cents_str(card_target), "remeasurement_ars": cents_str(diff_card)},
    }


def summarize_journal(lines: list[Line]) -> tuple[list[dict], int, int]:
    """Summary entry: one line per account, net on its side. Raises if debits != credits."""
    total_d = sum(ln.debe for ln in lines)
    total_h = sum(ln.haber for ln in lines)
    if total_d != total_h:
        raise BalanceError(f"journal does not balance: debe {total_d} haber {total_h}")
    by_acc: dict[str, int] = defaultdict(int)
    for ln in lines:
        by_acc[ln.account] += ln.debe - ln.haber
    rows = []
    for code in chart():
        if code not in by_acc or by_acc[code] == 0:
            continue
        net = by_acc[code]
        rows.append({"account": code, "name": account_name(code),
                     "debe": cents_str(max(net, 0)), "haber": cents_str(max(-net, 0))})
    sd = sum(to_cents(r["debe"]) for r in rows)
    sh = sum(to_cents(r["haber"]) for r in rows)
    if sd != sh:
        raise BalanceError(f"summary entry does not balance: debe {sd} haber {sh}")
    return rows, sd, sh


# ---------- exceptions ----------

def build_exceptions(txns: list[Txn], receipts: dict[str, dict]) -> list[dict]:
    out = []
    for t in txns:
        for code in t.exceptions:
            if code == "original_in_review":
                continue
            out.append({"txn_id": t.id, "type": code})
    for rid, r in sorted(receipts.items()):
        if r.get("unreadable"):
            out.append({"txn_id": None, "receipt_id": rid, "type": "receipt_unreadable"})
    unmatched = sorted(set(receipts) - {t.receipt_id for t in txns if t.receipt_id})
    for rid in unmatched:
        if not receipts[rid].get("unreadable"):
            out.append({"txn_id": None, "receipt_id": rid, "type": "receipt_unmatched"})
    for i, e in enumerate(out, 1):
        e["id"] = f"EX-{i:03d}"
    return out


# ---------- run ----------

def run(receipts: dict[str, dict], ai: dict[str, dict] | None = None,
        threshold: Decimal | None = None) -> dict:
    txns = load_export()
    apply_rules(txns)
    match_receipts(txns, receipts)
    detect_duplicates(txns)
    detect_missing_receipts(txns)
    detect_amount_mismatches(txns)
    link_refunds(txns)
    resolve(txns, ai, threshold)
    lines, balances = build_journal(txns)
    summary_rows, total_d, total_h = summarize_journal(lines)
    exceptions = build_exceptions(txns, receipts)
    return {
        "txns": txns,
        "lines": lines,
        "balances": balances,
        "entry": summary_rows,
        "entry_totals": {"debe": cents_str(total_d), "haber": cents_str(total_h),
                         "balanced": total_d == total_h},
        "exceptions": exceptions,
        "receipts": receipts,
        "threshold": str(threshold) if threshold is not None else None,
    }


def txn_dict(t: Txn) -> dict:
    d = asdict(t)
    d.pop("raw")
    d["posted_at"] = t.posted_at.isoformat()
    d["amount"] = cents_str(t.amount_cents)
    d.pop("amount_cents")
    d["rate"] = str(t.rate) if t.rate is not None else None
    d["ars"] = cents_str(t.ars_cents)
    d.pop("ars_cents")
    d["export"] = t.raw
    return d
