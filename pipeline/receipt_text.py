"""Receipt text and the deterministic template parser.

The template parser is the rules baseline for reading receipts. It knows the label words of
the layouts it was written for. The AI reader in pipeline/ai/extract.py is measured against
the same ground truth, so the two can be compared field by field.
"""

from __future__ import annotations

import re
from datetime import date
from functools import cache
from pathlib import Path

from pypdf import PdfReader

from pipeline.paths import RECEIPTS

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}

ES_AMOUNT = re.compile(r"(\d{1,3}(?:\.\d{3})*,\d{2})")
EN_AMOUNT = re.compile(r"(\d{1,3}(?:,\d{3})*\.\d{2})")
NUMBER = re.compile(r"\d[\d.,]*\d")


@cache
def text(receipt_id: str) -> str:
    return pdf_text(RECEIPTS / f"{receipt_id}.pdf")


def pdf_text(path: Path) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)


def receipt_ids() -> list[str]:
    return sorted(p.stem for p in RECEIPTS.glob("RC-*.pdf"))


def _amount(line: str) -> tuple[int, str] | None:
    """Returns (cents, number format) from a line, or None. The last separator decides the
    format: '1.234,56' is Spanish, '1,234.56' is English."""
    for token in NUMBER.findall(line):
        if ES_AMOUNT.fullmatch(token):
            whole, dec = token.replace(".", "").split(",")
            return int(whole) * 100 + int(dec), "es"
        if EN_AMOUNT.fullmatch(token):
            whole, dec = token.replace(",", "").split(".")
            return int(whole) * 100 + int(dec), "en"
    return None


def _date(lines: list[str]) -> date | None:
    joined = "\n".join(lines)
    m = re.search(r"Departure\s+(\d{2})-([A-Z]{3})-(\d{4})", joined)
    if m:
        return date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))
    m = re.search(r"(January|February|March|April|May|June|July|August|September|October|"
                  r"November|December) (\d{1,2}), (\d{4})", joined)
    if m:
        return date(int(m.group(3)), MONTHS[m.group(1)[:3].lower()], int(m.group(2)))
    m = re.search(r"Fecha:\s*(\d{2})/(\d{2})/(\d{4})", joined)
    if m:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", joined)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.search(r"Issue date\s+(\d{2})([A-Z]{3})(\d{2})", joined)
    if m:
        return date(2000 + int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))
    return None


def _currency(joined: str, number_format: str) -> str:
    if "USDC" in joined:
        return "USDC"
    if "€" in joined or re.search(r"\bEUR\b", joined):
        return "EUR"
    if "Pesos argentinos" in joined or re.search(r"\bARS\b", joined):
        return "ARS"
    return "USD"


def parse(receipt_text: str) -> dict:
    """Template parser. Returns vendor, date, amount and currency, any of them may be None."""
    lines = [ln.strip() for ln in receipt_text.splitlines() if ln.strip()]
    if not lines:
        return {"vendor": None, "date": None, "amount_cents": None, "currency": None}
    vendor = lines[1] if lines[0] == "COMPROBANTE DE PAGO" and len(lines) > 1 else lines[0]

    amount, fmt = None, "en"
    for label in ("Amount paid", "Total charges", "TOTAL", "Total"):
        idx = [i for i, ln in enumerate(lines) if ln == label]
        if idx:
            i = idx[-1]
            for ln in lines[i + 1:i + 2]:
                found = _amount(ln)
                if found:
                    amount, fmt = found
            if amount is not None:
                break
    joined = "\n".join(lines)
    d = _date(lines)
    return {
        "vendor": vendor,
        "date": d.isoformat() if d else None,
        "amount_cents": amount,
        "currency": _currency(joined, fmt) if amount is not None else None,
    }


def parse_all() -> dict[str, dict]:
    return {rid: {**parse(text(rid)), "source": "template_parser"} for rid in receipt_ids()}
