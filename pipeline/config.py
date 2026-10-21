from __future__ import annotations

from functools import cache

import yaml

from pipeline.paths import CONFIG


@cache
def settings() -> dict:
    return yaml.safe_load((CONFIG / "settings.yaml").read_text(encoding="utf-8"))


@cache
def chart() -> dict[str, dict]:
    data = yaml.safe_load((CONFIG / "chart_of_accounts.yaml").read_text(encoding="utf-8"))
    return {a["code"]: a for a in data["accounts"]}


@cache
def rules() -> dict:
    return yaml.safe_load((CONFIG / "rules.yaml").read_text(encoding="utf-8"))


def account_name(code: str) -> str:
    return chart()[code]["name"]


def ai_allowed_accounts() -> list[str]:
    return [code for code, a in chart().items() if a.get("ai_allowed")]
