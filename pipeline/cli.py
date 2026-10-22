"""Command line entry point: `uv run ctl <command>`. Each command prints a short summary."""

from __future__ import annotations

import argparse
import json
import sys


def _print(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def cmd_fx(_args) -> None:
    from pipeline import fx

    _print(fx.snapshot())


def cmd_generate(_args) -> None:
    from pipeline import generate

    _print(generate.build())


def cmd_close(_args) -> None:
    from pipeline import close, eval

    c = close.run()
    ev = eval.run(c)
    s = c["summary"]
    _print(
        {
            "receipt_source": s["receipt_source"],
            "transactions": s["transactions"],
            "totals": s["totals"],
            "split": s["split"],
            "no_rule": s["no_rule"],
            "exceptions": s["exceptions"],
            "threshold": s["threshold"],
            "entry_balanced": c["entry_totals"],
            "anomalies": {
                k: {
                    kk: vv
                    for kk, vv in v.items()
                    if kk in ("planted", "found", "true_positives", "false_positives", "caught_in_review")
                }
                if isinstance(v, dict)
                else v
                for k, v in ev["anomalies"].items()
            },
            "receipt_matching": {k: ev["receipt_matching"][k] for k in ("correct", "total", "accuracy")},
            "rules_accuracy": {k: ev["accounts"]["rules"][k] for k in ("correct", "total", "accuracy")},
            "template_parser_all_fields": ev["extraction"]["template_parser"]["per_field"]["all_fields"],
        }
    )


def _ai(step: str):
    def run(_args) -> None:
        import importlib

        from pipeline.ai import store

        mod = importlib.import_module(f"pipeline.ai.{step}")
        out = mod.run()
        usage = store.record_usage()
        _print({"result": out, "llm_calls_total": usage["total_calls"], "llm_cost_usd_total": usage["total_cost_usd"]})

    return run


def cmd_build(_args) -> None:
    """Full build in order. AI steps reuse their committed outputs and only call the model for
    what changed. Order: read receipts, match, suggest accounts, measure and pick the threshold,
    close, explain the exceptions that remain, close again with the explanations, measure."""
    from pipeline import close, eval
    from pipeline.ai import explain, extract, store, suggest

    steps = {}
    steps["extract"] = extract.run()
    close.run("ai")
    steps["suggest"] = suggest.run()
    eval.run(close.run("ai"))  # picks the threshold
    close.run("ai")
    steps["explain"] = explain.run()
    c = close.run("ai")
    usage = store.record_usage()
    ev = eval.run(c)
    try:
        from pipeline import site_data

        site_data.export(c, ev)
    except ImportError:
        pass
    s = c["summary"]
    _print(
        {
            "ai_steps": steps,
            "split": s["split"],
            "threshold": s["threshold"],
            "exceptions": s["exceptions"],
            "entry_balanced": c["entry_totals"]["balanced"],
            "llm_calls_total": usage["total_calls"],
            "llm_cost_usd_total": usage["total_cost_usd"],
        }
    )


def cmd_qbo_auth(_args) -> None:
    """Refresh the QuickBooks token (saved back to .env) and show the sandbox company. Never in CI."""
    from pipeline.qbo.client import Client, read_env

    _print(Client(read_env()).company())


def cmd_qbo_post(_args) -> None:
    """Post the close to the QuickBooks sandbox (once), read it back and verify it. Never in CI."""
    from pipeline.qbo import post

    r = post.run()
    keys = ("action", "doc_number", "qbo_entry_id", "lines", "entry_total_debit", "entry_total_credit")
    keys += ("lines_total_debit", "lines_total_credit", "checks", "result")
    _print({k: r[k] for k in keys})


COMMANDS = {
    "build": (cmd_build, "full pipeline: AI steps (cached), close, eval, site data"),
    "fx": (cmd_fx, "download the exchange rate snapshot"),
    "ai-extract": (_ai("extract"), "AI reads every receipt (build time, cached)"),
    "ai-suggest": (_ai("suggest"), "AI suggests accounts where no rule applies (cached)"),
    "ai-explain": (_ai("explain"), "AI explains each exception, verified (cached)"),
    "generate": (cmd_generate, "write the synthetic month and its ground truth"),
    "close": (cmd_close, "run the close, write close.json, the Excel and eval.json"),
    "qbo-auth": (cmd_qbo_auth, "refresh the QuickBooks sandbox token and show the company"),
    "qbo-post": (cmd_qbo_post, "post the entry to the QuickBooks sandbox once, read it back, verify it"),
}


def main(argv: list[str] | None = None) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="ctl")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, (_fn, help_text) in COMMANDS.items():
        sub.add_parser(name, help=help_text)
    args = parser.parse_args(argv)
    COMMANDS[args.command][0](args)


if __name__ == "__main__":
    main()
