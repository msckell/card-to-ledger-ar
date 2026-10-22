"""Post the month's journal entry to the QuickBooks Online sandbox, read it back, verify it.

The entry comes from `data/out/close.json` as it is: one QuickBooks line per journal line, the
same peso amounts, never recomputed or rounded. The entry is in ARS (`CurrencyRef`) with the
month end rate from our snapshot expressed the way QuickBooks wants it (USD per ARS). QuickBooks
shows a USD equivalent next to it, which it calculates itself and which we do not check.

Idempotent: the entry carries a fixed DocNumber. If an entry with that number exists, nothing is
posted and the existing entry is verified.

Verified to the cent: line count, every line by its journal line ID, debits and credits per
account and the totals. The entry in close.json nets each account (one side per account), so the
netted totals are compared with `entry_totals` and the gross line totals with the journal lines.

The result goes to `data/out/qbo_post.json`, which never holds tokens or the company ID.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal

import yaml

from pipeline import config
from pipeline.jsonio import read_json, write_json
from pipeline.money import cents_str, to_cents
from pipeline.paths import CONFIG, OUT
from pipeline.qbo.client import Client, QboError, read_env

MAPPING_FILE = CONFIG / "quickbooks_accounts.yaml"
RESULT_FILE = OUT / "qbo_post.json"


def load_mapping() -> dict:
    return yaml.safe_load(MAPPING_FILE.read_text(encoding="utf-8"))


def unmapped_accounts(close: dict, mapping: dict) -> list[str]:
    """Codes used in the entry (or in the chart) with no QuickBooks account."""
    used = {line["account"] for line in close["journal_lines"]} | {e["account"] for e in close["entry"]}
    return sorted((used | set(config.chart())) - set(mapping["accounts"]))


def dumps_exact(obj) -> str:
    """JSON where every Decimal is written with its exact digits as a JSON number, never a float."""

    def mark(o):
        if isinstance(o, Decimal):
            return f"__DEC__{o}__"
        if isinstance(o, dict):
            return {k: mark(v) for k, v in o.items()}
        if isinstance(o, list):
            return [mark(v) for v in o]
        if isinstance(o, float):
            raise TypeError("float in a QuickBooks payload")
        return o

    text = json.dumps(mark(obj), ensure_ascii=False)
    return re.sub(r'"__DEC__([-0-9.]+)__"', r"\1", text)


def exchange_rate(close: dict) -> Decimal:
    """QuickBooks wants home currency units (USD) per one ARS. Our snapshot gives ARS per USD."""
    return Decimal(1) / Decimal(close["balances"]["closing_rate"])


def line_description(line: dict) -> str:
    parts = [line["id"], line["txn_id"], line["date"], line["detail"]]
    if line["status"] != "posted":
        parts.append(line["status"])
    return " · ".join(parts)


def build_payload(close: dict, mapping: dict, account_ids: dict[str, str]) -> dict:
    if missing := unmapped_accounts(close, mapping):
        raise QboError(f"accounts with no QuickBooks mapping: {', '.join(missing)}")
    lines = []
    for jl in close["journal_lines"]:
        debit, credit = to_cents(jl["debe"]), to_cents(jl["haber"])
        if (debit == 0) == (credit == 0):
            raise QboError(f"{jl['id']} must have exactly one of debit or credit")
        lines.append(
            {
                "DetailType": "JournalEntryLineDetail",
                "Amount": Decimal(cents_str(debit or credit)),
                "Description": line_description(jl),
                "JournalEntryLineDetail": {
                    "PostingType": "Debit" if debit else "Credit",
                    "AccountRef": {"value": account_ids[jl["account"]]},
                },
            }
        )
    debits = sum(to_cents(jl["debe"]) for jl in close["journal_lines"])
    credits = sum(to_cents(jl["haber"]) for jl in close["journal_lines"])
    if debits != credits:
        raise QboError("journal lines do not balance, nothing posted")
    _check_entry_matches_lines(close)
    period = close["summary"]["period"]
    return {
        "DocNumber": mapping["doc_number"],
        "TxnDate": max(jl["date"] for jl in close["journal_lines"]),
        "CurrencyRef": {"value": mapping["company_currency"]},
        "ExchangeRate": exchange_rate(close),
        "PrivateNote": (
            f"Card to Ledger AR · {period} close of {close['summary']['company']} "
            "(fictional company, synthetic data) · source data/out/close.json"
        ),
        "Line": lines,
    }


def _gross_by_account(close: dict) -> dict[str, list[int]]:
    """[debits, credits] in cents per account, summed over the journal lines."""
    out = defaultdict(lambda: [0, 0])
    for jl in close["journal_lines"]:
        out[jl["account"]][0] += to_cents(jl["debe"])
        out[jl["account"]][1] += to_cents(jl["haber"])
    return out


def _net(pair: list[int]) -> list[int]:
    """Gross debits and credits of one account netted to one side, the way the entry shows it."""
    diff = pair[0] - pair[1]
    return [max(diff, 0), max(-diff, 0)]


def _check_entry_matches_lines(close: dict) -> None:
    """The entry in close.json nets each account. It must agree with its own journal lines."""
    gross = _gross_by_account(close)
    for e in close["entry"]:
        if [to_cents(e["debe"]), to_cents(e["haber"])] != _net(gross[e["account"]]):
            raise QboError(f"close.json entry and journal lines disagree on {e['account']}, nothing posted")
    if set(gross) - {e["account"] for e in close["entry"]}:
        raise QboError("journal lines use an account missing from the entry, nothing posted")


def _quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def ensure_currency(client: Client, code: str) -> None:
    prefs = client.company()
    if not prefs["multicurrency_enabled"]:
        raise QboError("multicurrency is off in the sandbox company. Turn it on in Account and settings.")
    if prefs["home_currency"] == code:
        return
    active = {c["Code"] for c in client.query("select * from CompanyCurrency").get("CompanyCurrency", [])}
    if code not in active:
        client.request("POST", "companycurrency", body=dumps_exact({"Code": code}))


def ensure_accounts(client: Client, mapping: dict) -> tuple[dict[str, str], list[str]]:
    """QuickBooks account ID per code. Reuses an account with the same name, creates the rest.
    An existing account with a different type or currency stops the run."""
    ids, created = {}, []
    for code, want in mapping["accounts"].items():
        found = client.query(f"select * from Account where Name = '{_quote(want['name'])}'").get("Account", [])
        if found:
            acct = found[0]
            currency = (acct.get("CurrencyRef") or {}).get("value")
            expected_currency = want.get("currency") or client.company()["home_currency"]
            if (acct["AccountType"], acct.get("AccountSubType"), currency) != (
                want["type"],
                want["detail_type"],
                expected_currency,
            ):
                raise QboError(
                    f"account '{want['name']}' exists as {acct['AccountType']} / {acct.get('AccountSubType')} "
                    f"/ {currency}, the mapping says {want['type']} / {want['detail_type']} / {expected_currency}"
                )
        else:
            body = {
                "Name": want["name"],
                "AccountType": want["type"],
                "AccountSubType": want["detail_type"],
                "Description": config.account_name(code)[:100],
            }
            if want.get("currency"):
                body["CurrencyRef"] = {"value": want["currency"]}
            acct = client.request("POST", "account", body=dumps_exact(body))["Account"]
            created.append(code)
        ids[code] = acct["Id"]
    return ids, created


def find_existing(client: Client, doc_number: str) -> list[dict]:
    q = f"select * from JournalEntry where DocNumber = '{_quote(doc_number)}'"
    return client.query(q).get("JournalEntry", [])


def verify(close: dict, je: dict, account_ids: dict[str, str]) -> dict:
    """Compare the entry QuickBooks holds against close.json, in cents. Three levels: every line
    by its journal line ID, debits and credits per account (gross and netted like the entry) and
    the totals."""
    _check_entry_matches_lines(close)
    code_of = {v: k for k, v in account_ids.items()}
    lines = [ln for ln in je.get("Line", []) if ln.get("DetailType") == "JournalEntryLineDetail"]

    got_by_id, got = {}, defaultdict(lambda: [0, 0])
    unknown_accounts = set()
    for ln in lines:
        d = ln["JournalEntryLineDetail"]
        code = code_of.get(d["AccountRef"]["value"])
        if code is None:
            unknown_accounts.add(d["AccountRef"]["value"])
            continue
        cents = to_cents(ln["Amount"])
        side = 0 if d["PostingType"] == "Debit" else 1
        got[code][side] += cents
        got_by_id[(ln.get("Description") or "").split(" · ")[0]] = (code, side, cents)

    line_mismatches = []
    for jl in close["journal_lines"]:
        debit, credit = to_cents(jl["debe"]), to_cents(jl["haber"])
        if got_by_id.get(jl["id"]) != (jl["account"], 0 if debit else 1, debit or credit):
            line_mismatches.append(jl["id"])

    want = _gross_by_account(close)
    entry = {e["account"]: [to_cents(e["debe"]), to_cents(e["haber"])] for e in close["entry"]}
    per_account = []
    for code in sorted(set(want) | set(got)):
        net = _net(got[code])
        per_account.append(
            {
                "account": code,
                "name": config.account_name_en(code),
                "entry_debit": cents_str(entry.get(code, [0, 0])[0]),
                "entry_credit": cents_str(entry.get(code, [0, 0])[1]),
                "qbo_net_debit": cents_str(net[0]),
                "qbo_net_credit": cents_str(net[1]),
                "lines_debit": cents_str(want[code][0]),
                "lines_credit": cents_str(want[code][1]),
                "qbo_debit": cents_str(got[code][0]),
                "qbo_credit": cents_str(got[code][1]),
                "match": got[code] == want[code] and net == entry.get(code),
            }
        )
    lines_debit = sum(p[0] for p in want.values())
    lines_credit = sum(p[1] for p in want.values())
    qbo_debit = sum(p[0] for p in got.values())
    qbo_credit = sum(p[1] for p in got.values())
    net_debit = sum(_net(p)[0] for p in got.values())
    net_credit = sum(_net(p)[1] for p in got.values())
    checks = {
        "currency": (je.get("CurrencyRef") or {}).get("value") == "ARS",
        "line_count": len(lines) == len(close["journal_lines"]),
        "every_line": not line_mismatches and not unknown_accounts,
        "per_account": all(a["match"] for a in per_account),
        "lines_total": (qbo_debit, qbo_credit) == (lines_debit, lines_credit),
        "entry_total": cents_str(net_debit) == close["entry_totals"]["debe"]
        and cents_str(net_credit) == close["entry_totals"]["haber"],
        "balanced": qbo_debit == qbo_credit and net_debit == net_credit,
    }
    return {
        "lines": len(lines),
        "close_lines": len(close["journal_lines"]),
        "lines_total_debit": cents_str(qbo_debit),
        "lines_total_credit": cents_str(qbo_credit),
        "entry_total_debit": cents_str(net_debit),
        "entry_total_credit": cents_str(net_credit),
        "close_entry_total": close["entry_totals"]["debe"],
        "accounts": len(per_account),
        "per_account": per_account,
        "line_mismatches": line_mismatches[:20],
        "checks": checks,
        "result": "pass" if all(checks.values()) else "fail",
    }


def run(client: Client | None = None, close: dict | None = None) -> dict:
    close = close or read_json(OUT / "close.json")
    mapping = load_mapping()
    if missing := unmapped_accounts(close, mapping):
        raise QboError(f"accounts with no QuickBooks mapping: {', '.join(missing)}")
    client = client or Client(read_env())

    ensure_currency(client, mapping["company_currency"])
    account_ids, created = ensure_accounts(client, mapping)
    doc = mapping["doc_number"]

    existing = find_existing(client, doc)
    if len(existing) > 1:
        raise QboError(f"{len(existing)} journal entries carry DocNumber {doc}. Fix the sandbox by hand first.")
    if existing:
        je_id, action = existing[0]["Id"], "already posted, verified only"
    else:
        payload = build_payload(close, mapping, account_ids)
        je_id = client.request("POST", "journalentry", body=dumps_exact(payload))["JournalEntry"]["Id"]
        action = "posted"

    je = client.request("GET", f"journalentry/{je_id}")["JournalEntry"]
    check = verify(close, je, account_ids)
    company = client.company()
    result = {
        "environment": "sandbox",
        "company": company["company_name"],
        "home_currency": company["home_currency"],
        "doc_number": je.get("DocNumber"),
        "qbo_entry_id": je_id,
        "txn_date": je.get("TxnDate"),
        "posted_at": je.get("MetaData", {}).get("CreateTime"),
        "verified_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "action": action,
        "currency": (je.get("CurrencyRef") or {}).get("value"),
        "exchange_rate_usd_per_ars": str(je.get("ExchangeRate")),
        "closing_rate_ars_per_usd": close["balances"]["closing_rate"],
        "accounts_created": created,
        **check,
    }
    write_json(RESULT_FILE, result)
    if check["result"] != "pass":
        failed = [k for k, ok in check["checks"].items() if not ok]
        raise QboError(f"read back does not match close.json: {', '.join(failed)}. See {RESULT_FILE.name}.")
    return result
