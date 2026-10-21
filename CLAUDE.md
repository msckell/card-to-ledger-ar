# CLAUDE.md · Card to Ledger AR

Instructions for AI coding agents working in this repo. Read this first, then `STATUS.md` for the current state. `README.md` explains the project for humans.

## What this repo is

A month end close in Argentine pesos for a fictional company (Andes Labs SRL) that spends in US dollars with a corporate card and pays foreign contractors in USDC. Deterministic rules do everything they can, AI handles only what rules cannot, a person reviews the rest, and every split is measured against a ground truth written by the data generator.

Independent prototype. Synthetic data, an assumed export format, real exchange rates from a public source. Taxes are out of scope.

## Commands

```sh
uv sync
uv run ruff check . && uv run ruff format --check .
uv run pytest                 # offline
uv run ctl fx                 # refresh the rate snapshot (committed, optional)
uv run ctl generate           # synthetic month and ground truth
uv run ctl build              # AI steps (cached), close, eval, site data, memo and README
cd site && npm ci && npm run build
```

`uv run ctl --help` lists every subcommand. CI (`.github/workflows/ci.yml`) runs ruff, pytest and the site build. Run the same before you commit.

## Layout

- `config/`: chart of accounts (`chart_of_accounts.yaml`), merchant rules (`rules.yaml`), period, rate convention and thresholds (`settings.yaml`).
- `pipeline/`: the deterministic engine.
  - `generate.py`, `receipts_pdf.py`: synthetic movements, receipt PDFs and ground truth.
  - `fx.py`, `money.py`: rate snapshot and Decimal money.
  - `engine.py`, `close.py`: matching, anomaly detection, account rules, journal entry.
  - `eval.py`: scores every step against the ground truth and sweeps the confidence threshold.
  - `excel.py`, `site_data.py`, `methodology.py`: outputs.
  - `ai/`: the three LLM steps (`extract.py`, `suggest.py`, `explain.py`), the verifier (`verifier.py`), the cache (`store.py`) and the single entry point to Claude (`llm.py`).
- `data/`: committed outputs. `data/truth/` is the ground truth, `data/ai/` the cached LLM outputs, `data/site/site.json` what the page reads.
- `docs/`: `memo.template.md` and `README.template.md`. The build fills in their numbers and writes `docs/memo.md` and `README.md`. Edit the templates, never the outputs.
- `site/`: static Vite + React + TypeScript + Tailwind page. It reads only `site.json`. Sections tell one story in order: hero, problem, result flow, how it works, three real examples, rules or AI, review queue, journal entry, methodology, memo.
- `tests/`: pytest, offline.

## Rules that must not be broken

**Numbers**
- Every figure and status comes from deterministic code and is rendered by templates. The LLM never types a number.
- Money is `Decimal` and integer cents. Never `float`. Round only when displaying.
- The journal entry must balance to the cent. The build stops otherwise.
- A failed source is never a zero. If a source fails, say so and stop. Never invent rates.
- Rates are read only from the snapshot in `data/fx/`, with its source URL and download date.

**AI**
- AI is used in three places only: reading receipts, suggesting an account when no rule applies (from the allowed list, as an enum), and explaining exceptions. Each one is measured in `data/eval.json`.
- The AI never sees the ground truth.
- An extracted amount that differs from the charge becomes an exception, never a silent fix.
- All LLM calls happen at build time and their outputs are committed. No live LLM on the page.

**Verifier**
- `pipeline/ai/verifier.py` rejects raw figures, IDs outside the facts given, and banned claims ("approved", "compliant", "reconciled" and similar). Up to two retries with feedback, then the template only. Add a test whenever you change what it accepts.

**Method**
- Every assumption carries a label: documented, assumption, or out of scope. The rate convention and the USDC valuation are assumptions to validate with an accountant.
- Rules deliberately do not cover every merchant. Do not add rules just to raise the measured accuracy.

**Publishing**
- The page keeps `noindex,nofollow`, a `robots.txt` that disallows everything and the `X-Robots-Tag` header in `site/vercel.json`.
- Visual identity: black, white and an own gold (tokens in `site/src/index.css`), inspired by the audience's aesthetic but never their exact brand colors, logo or fonts. Chart colors for rules, AI and a person were checked with a colorblind palette validator and always carry direct labels.
- The data is synthetic and the page says so. Never imply the company is a real customer or describe how any real company works internally.

**Repo**
- Never commit secrets. Keys live in `.env` (gitignored). Update `.env.example` when you add a variable.
- No destructive git operations (force push, history rewrite) without explicit approval.

## Conventions

- Code, comments, commit messages, README, page and memo: English.
- Accounting labels an Argentine accountant reads (chart of accounts, journal entry columns, Excel sheet names): Spanish.
- Prose on the page, README and memo uses no dashes and no semicolons.
- Every number on the page, README and memo is read from `data/`. None is hardcoded.

## When you finish a task

Rewrite `STATUS.md` (do not append to it): what is done, what is next, open questions. It must fit on one screen.
