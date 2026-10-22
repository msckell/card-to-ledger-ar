"""QuickBooks handoff, offline. A fake sandbox answers through httpx.MockTransport."""

from __future__ import annotations

import json
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from pipeline import config
from pipeline.jsonio import read_json
from pipeline.money import to_cents
from pipeline.paths import OUT
from pipeline.qbo import post
from pipeline.qbo.client import Client, QboError, base_url, save_env_value

REALM = "9876543210123456"
ENV = {
    "QBO_CLIENT_ID": "id",
    "QBO_CLIENT_SECRET": "secret",
    "QBO_REFRESH_TOKEN": "old-refresh",
    "QBO_REALM_ID": REALM,
    "QBO_ENVIRONMENT": "sandbox",
}


@pytest.fixture(scope="module")
def close() -> dict:
    return read_json(OUT / "close.json")


class FakeSandbox:
    """Just enough of the QuickBooks Online API: token, company, preferences, queries, currency,
    accounts and journal entries. `tamper` changes the entry it returns on read back."""

    def __init__(self, tamper=None):
        self.accounts: dict[str, dict] = {}
        self.entries: dict[str, dict] = {}
        self.currencies: set[str] = set()
        self.posted_bodies: list[str] = []
        self.tamper = tamper

    def __call__(self, request: httpx.Request) -> httpx.Response:
        url = urlparse(str(request.url))
        if url.netloc == "oauth.platform.intuit.com":
            return httpx.Response(200, json={"access_token": "access", "refresh_token": "new-refresh"})
        assert url.netloc.startswith("sandbox-")
        assert parse_qs(url.query)["minorversion"] == ["75"]
        path = url.path.split(f"/company/{REALM}/")[1]
        if path.startswith("companyinfo"):
            return httpx.Response(200, json={"CompanyInfo": {"CompanyName": "Sandbox Company US", "Country": "US"}})
        if path == "preferences":
            prefs = {"MultiCurrencyEnabled": True, "HomeCurrency": {"value": "USD"}}
            return httpx.Response(200, json={"Preferences": {"CurrencyPrefs": prefs}})
        if path == "query":
            return httpx.Response(
                200, content=post.dumps_exact({"QueryResponse": self.query(parse_qs(url.query)["query"][0])})
            )
        body = request.content.decode()
        if path == "companycurrency":
            self.currencies.add(json.loads(body)["Code"])
            return httpx.Response(200, json={"CompanyCurrency": {"Code": "ARS"}})
        if path == "account":
            acct = {**json.loads(body), "Id": str(100 + len(self.accounts))}
            acct.setdefault("CurrencyRef", {"value": "USD"})
            self.accounts[acct["Name"]] = acct
            return httpx.Response(200, json={"Account": acct})
        if path == "journalentry":
            self.posted_bodies.append(body)
            je = {**json.loads(body, parse_float=Decimal), "Id": str(900 + len(self.entries))}
            je["MetaData"] = {"CreateTime": "2026-10-22T10:00:00-07:00"}
            self.entries[je["Id"]] = je
            return httpx.Response(200, content=post.dumps_exact({"JournalEntry": je}))
        if path.startswith("journalentry/"):
            je = json.loads(post.dumps_exact(self.entries[path.split("/")[1]]), parse_float=Decimal)
            if self.tamper:
                self.tamper(je)
            # Real QuickBooks answers with JSON numbers, so the fake does too.
            return httpx.Response(200, content=post.dumps_exact({"JournalEntry": je}))
        raise AssertionError(f"unexpected call {request.method} {path}")

    def query(self, sql: str) -> dict:
        value = sql.split("= '", 1)[1].rstrip("'").replace("\\'", "'") if "= '" in sql else None
        if "from Account" in sql:
            return {"Account": [self.accounts[value]]} if value in self.accounts else {}
        if "from JournalEntry" in sql:
            found = [je for je in self.entries.values() if je["DocNumber"] == value]
            return {"JournalEntry": found} if found else {}
        if "from CompanyCurrency" in sql:
            return {"CompanyCurrency": [{"Code": c} for c in self.currencies]}
        raise AssertionError(sql)


def _client(fake: FakeSandbox, tmp_path) -> Client:
    env_path = tmp_path / ".env"
    env_path.write_text("QBO_REFRESH_TOKEN=old-refresh\nOTHER=keep\n", encoding="utf-8")
    return Client(dict(ENV), http=httpx.Client(transport=httpx.MockTransport(fake)), env_path=env_path)


@pytest.fixture
def no_result_file(tmp_path, monkeypatch):
    monkeypatch.setattr(post, "RESULT_FILE", tmp_path / "qbo_post.json")
    return tmp_path / "qbo_post.json"


def test_every_account_used_has_a_mapping(close):
    mapping = post.load_mapping()
    assert post.unmapped_accounts(close, mapping) == []
    assert set(mapping["accounts"]) == set(config.chart())
    for code, acct in mapping["accounts"].items():
        assert acct["name"].startswith(code)
        assert ":" not in acct["name"] and '"' not in acct["name"]


def test_missing_mapping_stops_before_any_request(close):
    mapping = post.load_mapping()
    mapping["accounts"].pop("5.1.04")
    assert post.unmapped_accounts(close, mapping) == ["5.1.04"]
    with pytest.raises(QboError, match="no QuickBooks mapping"):
        post.build_payload(close, mapping, {})


def test_payload_balances_and_keeps_every_line(close):
    mapping = post.load_mapping()
    ids = {code: str(i) for i, code in enumerate(mapping["accounts"])}
    payload = post.build_payload(close, mapping, ids)
    assert len(payload["Line"]) == len(close["journal_lines"])
    sides = {"Debit": 0, "Credit": 0}
    for line, jl in zip(payload["Line"], close["journal_lines"], strict=True):
        sides[line["JournalEntryLineDetail"]["PostingType"]] += to_cents(line["Amount"])
        assert line["Description"].startswith(jl["id"])
        assert to_cents(line["Amount"]) == to_cents(jl["debe"]) + to_cents(jl["haber"])
    assert sides["Debit"] == sides["Credit"]
    assert payload["CurrencyRef"] == {"value": "ARS"}
    assert payload["ExchangeRate"] * Decimal(close["balances"]["closing_rate"]) == pytest.approx(Decimal(1))


def test_amounts_are_exact_decimals_never_floats(close):
    mapping = post.load_mapping()
    payload = post.build_payload(close, mapping, {code: "1" for code in mapping["accounts"]})
    assert all(isinstance(line["Amount"], Decimal) for line in payload["Line"])
    text = post.dumps_exact(payload)
    first = close["journal_lines"][0]["debe"]
    assert f'"Amount": {first},' in text  # digits as written in close.json, trailing zeros kept
    with pytest.raises(TypeError):
        post.dumps_exact({"Amount": 1.5})


def test_post_then_second_run_does_not_post_twice(close, tmp_path, no_result_file):
    fake = FakeSandbox()
    first = post.run(_client(fake, tmp_path), close)
    assert first["action"] == "posted"
    assert first["result"] == "pass"
    assert first["entry_total_debit"] == close["entry_totals"]["debe"]
    assert len(fake.accounts) == len(post.load_mapping()["accounts"])
    assert fake.currencies == {"ARS"}

    second = post.run(_client(fake, tmp_path), close)
    assert second["action"] == "already posted, verified only"
    assert second["qbo_entry_id"] == first["qbo_entry_id"]
    assert len(fake.posted_bodies) == 1
    assert second["accounts_created"] == []


def test_result_file_has_no_secrets_or_realm(close, tmp_path, no_result_file):
    post.run(_client(FakeSandbox(), tmp_path), close)
    text = no_result_file.read_text(encoding="utf-8")
    for secret in (REALM, "secret", "old-refresh", "new-refresh", '"access"'):
        assert secret not in text
    assert not any(k.lower().startswith(("realm", "token")) for k in read_json(no_result_file))


def test_refresh_token_is_saved_back(close, tmp_path, no_result_file):
    client = _client(FakeSandbox(), tmp_path)
    post.run(client, close)
    saved = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "QBO_REFRESH_TOKEN=new-refresh" in saved
    assert "OTHER=keep" in saved


def test_read_back_mismatch_fails(close, tmp_path, no_result_file):
    def shave_a_cent(je):
        line = je["Line"][0]
        line["Amount"] -= Decimal("0.01")

    with pytest.raises(QboError, match="does not match"):
        post.run(_client(FakeSandbox(tamper=shave_a_cent), tmp_path), close)
    result = read_json(no_result_file)
    assert result["result"] == "fail"
    assert result["checks"]["every_line"] is False
    assert result["checks"]["per_account"] is False


def test_read_back_missing_line_fails(close, tmp_path, no_result_file):
    with pytest.raises(QboError, match="line_count"):
        post.run(_client(FakeSandbox(tamper=lambda je: je["Line"].pop()), tmp_path), close)


def test_existing_account_with_other_type_stops(close, tmp_path, no_result_file):
    fake = FakeSandbox()
    name = post.load_mapping()["accounts"]["2.1.01"]["name"]
    fake.accounts[name] = {"Name": name, "Id": "7", "AccountType": "Bank", "AccountSubType": "Checking"}
    with pytest.raises(QboError, match="exists as Bank"):
        post.run(_client(fake, tmp_path), close)
    assert fake.posted_bodies == []


def test_only_sandbox_is_allowed():
    assert base_url({"QBO_ENVIRONMENT": "sandbox"}).startswith("https://sandbox-")
    with pytest.raises(QboError):
        base_url({"QBO_ENVIRONMENT": "production"})
    with pytest.raises(QboError):
        base_url({"QBO_ENVIRONMENT": "sandbox", "QBO_BASE_URL": "https://quickbooks.api.intuit.com"})


def test_save_env_value_replaces_only_that_line(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# comment\nA=1\nQBO_REFRESH_TOKEN=x\n", encoding="utf-8")
    save_env_value("QBO_REFRESH_TOKEN", "y", env)
    assert env.read_text(encoding="utf-8") == "# comment\nA=1\nQBO_REFRESH_TOKEN=y\n"


def test_site_block_and_docs_skip_quickbooks_when_it_never_ran(tmp_path, monkeypatch):
    from pipeline import site_data

    monkeypatch.setattr(site_data, "OUT", tmp_path)
    assert site_data._quickbooks() is None
    site = read_json(site_data.SITE_DATA / "site.json")
    site.pop("quickbooks", None)
    vals = site_data.memo_values(site)
    for template in ("README.template.md", "memo.template.md"):
        text = site_data._fill(template, vals)
        assert "QuickBooks Online sandbox." not in text and "ERP handoff" not in text
        assert "{{" not in text
