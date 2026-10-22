"""OAuth 2.0 refresh and JSON requests against the QuickBooks Online Accounting API.

Sandbox only. The environment and base URL come from `.env` and default to the sandbox. Any
other environment stops the command before a request is made.

Intuit rotates the refresh token. Every refresh writes the token it returns back to `.env`
before anything else happens, so a crash later never loses it.
"""

from __future__ import annotations

import json
import os
from decimal import Decimal
from pathlib import Path

import httpx

from pipeline.paths import ROOT

ENV_FILE = ROOT / ".env"
TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
SANDBOX_BASE_URL = "https://sandbox-quickbooks.api.intuit.com"
# Intuit ignores minor versions below 75 since August 2025 and answers in 75.
MINOR_VERSION = "75"
REQUIRED = ("QBO_CLIENT_ID", "QBO_CLIENT_SECRET", "QBO_REFRESH_TOKEN", "QBO_REALM_ID")


class QboError(Exception):
    pass


def read_env(path: Path = ENV_FILE) -> dict[str, str]:
    """Values from `.env`, overridden by the process environment."""
    values: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip()
    for k in (*REQUIRED, "QBO_ENVIRONMENT", "QBO_BASE_URL"):
        if os.environ.get(k):
            values[k] = os.environ[k]
    return values


def save_env_value(key: str, value: str, path: Path = ENV_FILE) -> None:
    """Replace one `KEY=value` line in `.env` (or append it), written through a temp file."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    out, found = [], False
    for line in lines:
        if line.split("=", 1)[0].strip() == key:
            out.append(f"{key}={value}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"{key}={value}")
    tmp = path.with_suffix(".tmp")
    tmp.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(path)


def base_url(env: dict[str, str]) -> str:
    environment = env.get("QBO_ENVIRONMENT") or "sandbox"
    if environment != "sandbox":
        raise QboError(f"QBO_ENVIRONMENT is '{environment}'. Only the sandbox is allowed.")
    url = (env.get("QBO_BASE_URL") or SANDBOX_BASE_URL).rstrip("/")
    if not httpx.URL(url).host.startswith("sandbox-"):
        raise QboError(f"QBO_BASE_URL {url} is not a sandbox host.")
    return url


class Client:
    def __init__(self, env: dict[str, str], http: httpx.Client | None = None, env_path: Path = ENV_FILE):
        missing = [k for k in REQUIRED if not env.get(k)]
        if missing:
            raise QboError(f"missing in .env: {', '.join(missing)}")
        self.env = env
        self.env_path = env_path
        self.base = base_url(env)
        self.realm = env["QBO_REALM_ID"]
        self.http = http or httpx.Client(timeout=60)
        self.access_token: str | None = None

    def refresh(self) -> None:
        r = self.http.post(
            TOKEN_URL,
            auth=(self.env["QBO_CLIENT_ID"], self.env["QBO_CLIENT_SECRET"]),
            data={"grant_type": "refresh_token", "refresh_token": self.env["QBO_REFRESH_TOKEN"]},
            headers={"Accept": "application/json"},
        )
        if r.status_code != 200:
            raise QboError(f"token refresh failed ({r.status_code}): {r.text[:300]}")
        body = r.json()
        new_refresh = body.get("refresh_token")
        if new_refresh and new_refresh != self.env["QBO_REFRESH_TOKEN"]:
            save_env_value("QBO_REFRESH_TOKEN", new_refresh, self.env_path)
            self.env["QBO_REFRESH_TOKEN"] = new_refresh
        self.access_token = body["access_token"]

    def request(self, method: str, path: str, params: dict | None = None, body: str | None = None) -> dict:
        """One API call. Numbers in the response are parsed as Decimal, never float."""
        if self.access_token is None:
            self.refresh()
        url = f"{self.base}/v3/company/{self.realm}/{path}"
        headers = {"Authorization": f"Bearer {self.access_token}", "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        r = self.http.request(
            method, url, params={**(params or {}), "minorversion": MINOR_VERSION}, content=body, headers=headers
        )
        if r.status_code >= 400:
            raise QboError(f"{method} {path} failed ({r.status_code}): {r.text[:1500]}")
        return json.loads(r.text, parse_float=Decimal)

    def query(self, sql: str) -> dict:
        return self.request("GET", "query", params={"query": sql}).get("QueryResponse", {})

    def company(self) -> dict:
        """Company name, home currency and the multicurrency switch."""
        info = self.request("GET", f"companyinfo/{self.realm}")["CompanyInfo"]
        prefs = self.request("GET", "preferences")["Preferences"].get("CurrencyPrefs", {})
        return {
            "company_name": info.get("CompanyName"),
            "country": info.get("Country"),
            "home_currency": (prefs.get("HomeCurrency") or {}).get("value"),
            "multicurrency_enabled": prefs.get("MultiCurrencyEnabled", False),
        }
