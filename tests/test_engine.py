from datetime import date
from decimal import Decimal

import pytest

from pipeline import engine, fx
from pipeline.engine import BalanceError, Line, Txn
from pipeline.money import convert, fmt, to_cents


def _card(tid, day, desc, amount, **kw):
    return Txn(id=tid, posted_at=date(2026, 9, day), type=kw.pop("type", "card_purchase"),
               descriptor=desc, amount_cents=to_cents(amount), currency="USD",
               raw={"descriptor": desc}, **kw)


# ---------- money and FX ----------

def test_to_cents_refuses_fractions_of_a_cent():
    assert to_cents("1234.5") == 123450
    with pytest.raises(ValueError):
        to_cents("1.005")


def test_convert_rounds_half_up_once():
    assert convert(1, Decimal("1535.005")) == 1535  # 15.35005 ARS cents rounds to 1535
    assert convert(10, Decimal("0.05")) == 1  # 0.5 cents rounds up
    assert convert(4294, Decimal("1535")) == 6591290  # USD 42.94 at 1535 is ARS 65,912.90


def test_fx_reads_the_snapshot_seller_rate():
    rate = fx.rate(date(2026, 9, 30))
    assert rate == fx.official()[date(2026, 9, 30)].venta
    with pytest.raises(fx.FxError):
        fx.rate(date(2026, 1, 1))


def test_fmt_display():
    assert fmt(123456789) == "1,234,567.89"
    assert fmt(-5) == "-0.05"


# ---------- balance check ----------

def test_summary_entry_balances_and_nets_by_account():
    lines = [
        Line("JL-1", "T1", "2026-09-01", "5.1.01", 1000, 0, "", "", "", ""),
        Line("JL-2", "T1", "2026-09-01", "2.1.01", 0, 1000, "", "", "", ""),
        Line("JL-3", "T2", "2026-09-02", "2.1.01", 300, 0, "", "", "", ""),
        Line("JL-4", "T2", "2026-09-02", "5.1.01", 0, 300, "", "", "", ""),
    ]
    rows, d, h = engine.summarize_journal(lines)
    assert d == h == 700
    assert {r["account"]: (r["debe"], r["haber"]) for r in rows} == {
        "5.1.01": ("7.00", "0.00"), "2.1.01": ("0.00", "7.00")}


def test_unbalanced_journal_is_rejected():
    lines = [
        Line("JL-1", "T1", "2026-09-01", "5.1.01", 1000, 0, "", "", "", ""),
        Line("JL-2", "T1", "2026-09-01", "2.1.01", 0, 999, "", "", "", ""),
    ]
    with pytest.raises(BalanceError):
        engine.summarize_journal(lines)


def test_generated_close_balances():
    from pipeline.receipt_text import parse_all

    result = engine.run(parse_all())
    assert result["entry_totals"]["balanced"]
    assert result["entry_totals"]["debe"] == result["entry_totals"]["haber"]


# ---------- duplicates ----------

def test_duplicate_without_second_receipt_is_flagged():
    a = _card("T1", 10, "UBER *TRIP X1", "42.94", receipt_id="RC-1")
    b = _card("T2", 11, "UBER *TRIP X1", "42.94")
    engine.detect_duplicates([a, b])
    assert b.exceptions == ["duplicate_suspected"] and b.duplicate_of == "T1"
    assert a.exceptions == []


def test_same_amount_with_two_receipts_is_not_a_duplicate():
    a = _card("T1", 10, "UBER *TRIP X1", "12.00", receipt_id="RC-1")
    b = _card("T2", 10, "UBER *TRIP X1", "12.00", receipt_id="RC-2")
    engine.detect_duplicates([a, b])
    assert a.exceptions == [] and b.exceptions == []


def test_same_amount_far_apart_is_not_a_duplicate():
    a = _card("T1", 1, "SLACK T03AB12", "330.00", receipt_id="RC-1")
    b = _card("T2", 20, "SLACK T03AB12", "330.00")
    engine.detect_duplicates([a, b])
    assert b.exceptions == []


# ---------- refunds ----------

def test_full_refund_offsets_its_original_account():
    orig = _card("T1", 7, "FIGMA", "90.00", rule_id="R-011", rule_account="5.1.03", receipt_id="RC-1")
    ref = _card("T2", 10, "FIGMA", "90.00", type="card_refund")
    engine.link_refunds([orig, ref])
    engine.resolve([orig, ref], None, None)
    assert ref.refund_of == "T1"
    assert ref.exceptions == []
    assert ref.posted_account == "5.1.03" and ref.resolved_by == "rules"


def test_refund_lines_reverse_the_expense():
    orig = _card("T1", 7, "FIGMA", "90.00", rule_id="R-011", rule_account="5.1.03", receipt_id="RC-1")
    ref = _card("T2", 10, "FIGMA", "90.00", type="card_refund")
    engine.link_refunds([orig, ref])
    engine.resolve([orig, ref], None, None)
    lines = [ln for ln in engine.build_journal([orig, ref])[0] if ln.txn_id == "T2"]
    expense = next(ln for ln in lines if ln.account == "5.1.03")
    card = next(ln for ln in lines if ln.account == "2.1.01")
    assert expense.haber == card.debe == convert(9000, fx.rate(date(2026, 9, 10)))


def test_partial_refund_is_linked_but_sent_to_review():
    orig = _card("T1", 7, "AIRBNB * HM1", "800.00", rule_id="R-018", rule_account="5.1.05", receipt_id="RC-1")
    ref = _card("T2", 12, "AIRBNB * HM1", "120.00", type="card_refund")
    engine.link_refunds([orig, ref])
    engine.resolve([orig, ref], None, None)
    assert ref.refund_of == "T1"
    assert "refund_partial_link" in ref.exceptions
    assert ref.posted_account == engine.SUSPENSE


def test_refund_without_original_goes_to_review():
    ref = _card("T2", 8, "BOOKING.COM HOTEL", "210.00", type="card_refund")
    engine.link_refunds([ref])
    engine.resolve([ref], None, None)
    assert ref.exceptions == ["refund_original_not_found"]
    assert ref.posted_account == engine.SUSPENSE
