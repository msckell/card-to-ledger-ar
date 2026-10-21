"""One structured call to Claude, at build time only.

Two backends, same contract (system prompt, user prompt, Pydantic model in, validated model out):
- `api`: the Anthropic Python SDK with structured outputs, when ANTHROPIC_API_KEY is set.
- `cli`: Claude Code in headless mode (`claude -p --json-schema`), on the logged in Claude
  subscription. No API key needed.

Every call is counted in a process wide ledger that `usage()` returns.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

DEFAULT_MODEL = "claude-sonnet-5-5"
# Reading receipts is high volume and simple, so it defaults to the small model to stay under
# the USD 2 budget. Its accuracy is measured like every other step.
STEP_DEFAULTS = {"extract": "claude-haiku-5-5"}
# USD per million tokens (input, output), from the Anthropic pricing table, used only to
# estimate the cost of the API backend. The CLI backend reports its own estimate.
PRICES = {
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-opus-5-5": (4.0, 20.0),
    "claude-haiku-5-5": (0.10, 0.50),
}


class LlmError(Exception):
    pass


@dataclass
class Reply:
    data: BaseModel
    model: str
    backend: str
    duration_s: float
    cost_usd: float
    input_tokens: int
    output_tokens: int


_lock = threading.Lock()
_ledger: dict[str, dict] = {}


def _load_env() -> None:
    from pipeline.paths import ROOT

    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if v.strip() and k.strip() not in os.environ:
            os.environ[k.strip()] = v.strip()


_load_env()


def model_name(step: str = "") -> str:
    override = os.environ.get(f"ANTHROPIC_MODEL_{step.upper()}") if step else None
    if override:
        return override
    if step in STEP_DEFAULTS:
        return STEP_DEFAULTS[step]
    return os.environ.get("ANTHROPIC_MODEL") or DEFAULT_MODEL


def backend() -> str:
    return "api" if os.environ.get("ANTHROPIC_API_KEY") else "cli"


def ask(step: str, system: str, prompt: str, schema: type[BaseModel], max_tokens: int = 2000) -> Reply:
    start = time.monotonic()
    model = model_name(step)
    if backend() == "api":
        reply = _ask_api(model, system, prompt, schema, max_tokens)
    else:
        reply = _ask_cli(model, system, prompt, schema)
    reply.duration_s = round(time.monotonic() - start, 1)
    with _lock:
        row = _ledger.setdefault(step, {"calls": 0, "cost_usd": 0.0, "input_tokens": 0, "output_tokens": 0})
        row["calls"] += 1
        row["cost_usd"] += reply.cost_usd
        row["input_tokens"] += reply.input_tokens
        row["output_tokens"] += reply.output_tokens
    return reply


def failed_call(step: str) -> None:
    with _lock:
        row = _ledger.setdefault(step, {"calls": 0, "cost_usd": 0.0, "input_tokens": 0, "output_tokens": 0})
        row["calls"] += 1


def usage() -> dict:
    with _lock:
        return {k: dict(v) for k, v in _ledger.items()}


def _ask_api(model: str, system: str, prompt: str, schema: type[BaseModel], max_tokens: int) -> Reply:
    import anthropic

    client = anthropic.Anthropic()
    try:
        resp = client.messages.parse(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_format=schema,
        )
    except anthropic.APIStatusError as exc:
        raise LlmError(f"api error {exc.status_code}: {str(exc)[:200]}") from exc
    except anthropic.APIConnectionError as exc:
        raise LlmError(f"api connection error: {exc}") from exc
    if resp.stop_reason == "refusal" or resp.parsed_output is None:
        raise LlmError(f"no structured output (stop_reason={resp.stop_reason})")
    pin, pout = PRICES.get(model, (0.0, 0.0))
    cost = (resp.usage.input_tokens * pin + resp.usage.output_tokens * pout) / 1_000_000
    return Reply(resp.parsed_output, model, "api", 0.0, cost, resp.usage.input_tokens, resp.usage.output_tokens)


def _ask_cli(model: str, system: str, prompt: str, schema: type[BaseModel], timeout: int = 300) -> Reply:
    exe = shutil.which("claude")
    if exe is None:
        raise LlmError("claude CLI not found on PATH and no ANTHROPIC_API_KEY set")
    cmd = [
        exe,
        "-p",
        "--system-prompt",
        system,
        "--setting-sources",
        "",
        "--strict-mcp-config",
        "--tools",
        "",
        "--no-session-persistence",
        "--output-format",
        "json",
        "--model",
        model,
        "--json-schema",
        json.dumps(schema.model_json_schema()),
    ]
    try:
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise LlmError(f"claude timed out after {timeout}s") from exc
    if proc.returncode != 0 and not proc.stdout:
        raise LlmError(f"claude exit {proc.returncode}: {proc.stderr[:300]}")
    try:
        out = json.loads(proc.stdout)
    except ValueError as exc:
        raise LlmError(f"claude returned non JSON: {proc.stdout[:300]!r}") from exc
    if out.get("is_error") or not isinstance(out.get("structured_output"), dict):
        raise LlmError(f"claude error: {str(out.get('result'))[:300]}")
    try:
        data = schema.model_validate(out["structured_output"])
    except ValidationError as exc:
        raise LlmError(f"schema validation failed: {str(exc)[:300]}") from exc
    u = out.get("usage") or {}
    tokens_in = (
        int(u.get("input_tokens", 0))
        + int(u.get("cache_read_input_tokens", 0))
        + int(u.get("cache_creation_input_tokens", 0))
    )
    return Reply(
        data, model, "cli", 0.0, float(out.get("total_cost_usd") or 0.0), tokens_in, int(u.get("output_tokens", 0))
    )
