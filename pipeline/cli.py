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
    _print({
        "receipt_source": s["receipt_source"],
        "transactions": s["transactions"],
        "totals": s["totals"],
        "split": s["split"],
        "no_rule": s["no_rule"],
        "exceptions": s["exceptions"],
        "threshold": s["threshold"],
        "entry_balanced": c["entry_totals"],
        "anomalies": {k: {kk: vv for kk, vv in v.items() if kk in ("planted", "found", "true_positives",
                                                                    "false_positives", "caught_in_review")}
                      if isinstance(v, dict) else v for k, v in ev["anomalies"].items()},
        "receipt_matching": {k: ev["receipt_matching"][k] for k in ("correct", "total", "accuracy")},
        "rules_accuracy": {k: ev["accounts"]["rules"][k] for k in ("correct", "total", "accuracy")},
        "template_parser_all_fields": ev["extraction"]["template_parser"]["per_field"]["all_fields"],
    })


COMMANDS = {
    "fx": (cmd_fx, "download the exchange rate snapshot"),
    "generate": (cmd_generate, "write the synthetic month and its ground truth"),
    "close": (cmd_close, "run the close, write close.json, the Excel and eval.json"),
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
