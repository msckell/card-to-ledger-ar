"""Exchange rates: fetch once into a dated snapshot, then read only from the snapshot.

A failed source stops the build. Rates are never invented or filled with zeros.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from functools import cache

import httpx

from pipeline.config import settings
from pipeline.jsonio import write_json
from pipeline.paths import FX_DIR

OFFICIAL_CSV = FX_DIR / "usd_ars_oficial.csv"
CRYPTO_CSV = FX_DIR / "usd_ars_cripto.csv"
SOURCE_JSON = FX_DIR / "source.json"


class FxError(Exception):
    pass


def _fetch(url: str, start: str, end: str) -> list[dict]:
    resp = httpx.get(url, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    rows = [r for r in resp.json() if start <= r["fecha"] <= end]
    if not rows:
        raise FxError(f"no rows between {start} and {end} at {url}")
    for r in rows:
        if not r.get("compra") or not r.get("venta"):
            raise FxError(f"missing quote on {r.get('fecha')} at {url}")
    return sorted(rows, key=lambda r: r["fecha"])


def snapshot() -> dict:
    """Download both series and write the CSV snapshot plus its source record."""
    fx = settings()["fx"]
    start, end = fx["snapshot_from"], fx["snapshot_to"]
    FX_DIR.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name, url, path in (
        ("oficial", fx["source_url"], OFFICIAL_CSV),
        ("cripto", fx["crypto_source_url"], CRYPTO_CSV),
    ):
        rows = _fetch(url, start, end)
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(["fecha", "compra", "venta"])
            for r in rows:
                w.writerow([r["fecha"], str(Decimal(str(r["compra"]))), str(Decimal(str(r["venta"])))])
        summary[name] = {"url": url, "rows": len(rows), "from": rows[0]["fecha"], "to": rows[-1]["fecha"]}
    record = {
        "downloaded_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": "ArgentinaDatos (argentinadatos.com), public API, no key",
        "series": summary,
    }
    write_json(SOURCE_JSON, record)
    return record


@dataclass(frozen=True)
class Quote:
    compra: Decimal
    venta: Decimal


def _read(path) -> dict[date, Quote]:
    if not path.exists():
        raise FxError(f"missing FX snapshot {path.name}, run `ctl fx` first")
    out = {}
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out[date.fromisoformat(row["fecha"])] = Quote(Decimal(row["compra"]), Decimal(row["venta"]))
    return out


@cache
def official() -> dict[date, Quote]:
    return _read(OFFICIAL_CSV)


@cache
def crypto() -> dict[date, Quote]:
    return _read(CRYPTO_CSV)


def rate(day: date, series: str = "oficial") -> Decimal:
    """Rate on that exact day, on the configured side. A missing day is an error."""
    table = official() if series == "oficial" else crypto()
    if day not in table:
        raise FxError(f"no {series} rate for {day.isoformat()} in the snapshot")
    side = settings()["fx"]["rate_side"]
    return getattr(table[day], side)


def source_record() -> dict:
    return json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
