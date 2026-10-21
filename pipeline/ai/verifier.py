"""Rejects any AI explanation that could put a wrong number or a false claim in front of a reviewer.

Rules: no figures (digits, currency symbols or number words) outside cited IDs, no ID that is
not part of this exception, no claims of approval or compliance, at least one cited ID, and a
length cap. Numbers reach the reader only through the deterministic facts line.
"""

from __future__ import annotations

import re

ID_RX = re.compile(r"\b(?:TX|RC|EX|AI|JL)-\d{3,4}\b|\bR-(?:\d{3}|[A-Z]+)\b")
CITED_RX = re.compile(r"\[((?:TX|RC|EX|AI|JL)-\d{3,4}|R-(?:\d{3}|[A-Z]+))\]")
NUMBER_WORDS = re.compile(
    r"\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|"
    r"sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|"
    r"hundred|thousand|million|billion|percent|dozen)\b",
    re.IGNORECASE,
)
BANNED = re.compile(
    r"\b(approved?|approval|compliant|compliance|verified|reconciled|cleared|certified|audited|"
    r"guaranteed?|safe to post|no action needed|no issues?|fraud(?:ulent)?)\b",
    re.IGNORECASE,
)
MAX_CHARS = 450


def check(text: str, allowed_ids: set[str]) -> list[str]:
    violations = []
    found_ids = ID_RX.findall(text)
    for tok in found_ids:
        if tok not in allowed_ids:
            violations.append(f"invented_id: {tok}")
    stripped = ID_RX.sub("", text)
    for m in re.finditer(r"\d[\d.,]*", stripped):
        violations.append(f"raw_figure: {m.group(0)}")
    for sym in ("$", "€", "%"):
        if sym in stripped:
            violations.append(f"raw_figure: {sym}")
    for m in NUMBER_WORDS.finditer(stripped):
        violations.append(f"raw_figure: {m.group(0)}")
    for m in BANNED.finditer(text):
        violations.append(f"banned_claim: {m.group(0)}")
    if not any(c in allowed_ids for c in CITED_RX.findall(text)):
        violations.append("no_citation: cite at least one ID in square brackets")
    if len(text) > MAX_CHARS:
        violations.append(f"too_long: {len(text)} characters, the limit is {MAX_CHARS}")
    return violations
