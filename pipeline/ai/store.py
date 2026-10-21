"""Committed AI outputs under data/ai/ and the usage ledger."""

from __future__ import annotations

import os

from pipeline.ai import llm
from pipeline.jsonio import read_json, write_json
from pipeline.paths import AI_DIR


def load(name: str) -> dict | None:
    path = AI_DIR / name
    return read_json(path) if path.exists() else None


def save(name: str, data: dict) -> None:
    write_json(AI_DIR / name, data)


def workers() -> int:
    return int(os.environ.get("LLM_WORKERS", "6"))


def record_usage() -> dict:
    """Adds this run's calls to data/ai/usage.json, which keeps the running total."""
    current = load("usage.json") or {"backend": llm.backend(), "steps": {}}
    for step, row in llm.usage().items():
        acc = current["steps"].setdefault(step, {"calls": 0, "cost_usd": 0.0, "input_tokens": 0, "output_tokens": 0})
        for k in acc:
            acc[k] += row[k]
    current["models"] = {step: llm.model_name(step) for step in current["steps"]}
    current["total_calls"] = sum(r["calls"] for r in current["steps"].values())
    current["total_cost_usd"] = round(sum(r["cost_usd"] for r in current["steps"].values()), 4)
    for r in current["steps"].values():
        r["cost_usd"] = round(r["cost_usd"], 4)
    current["note"] = (
        "Cost is the API equivalent estimate. With the CLI backend the calls run on the Claude "
        "subscription and the figure is the estimate the CLI reports."
    )
    save("usage.json", current)
    return current
