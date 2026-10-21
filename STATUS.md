# STATUS · Card to Ledger AR

> Rewritten at the end of each task. Last update: 2026-10-21.

## Done
- Synthetic month, deterministic close engine, Excel export, AI layer with verifier, measured threshold, page, memo and README.
- One command rebuilds everything: `uv run ctl build` (AI outputs cached in `data/ai/`, 0 new calls when nothing changed).
- Page in `site/` builds clean and has no horizontal scroll at 375 px.
- QA: every number on the page traced to `data/site/site.json`. `noindex,nofollow` meta, `robots.txt` disallows all, `X-Robots-Tag` header. Secret scan over the full git history clean.
- Repo hygiene for publishing: short agent instructions in `CLAUDE.md`, `AGENTS.md` points to it, CI workflow, code formatted with ruff.

## Results (data/eval.json)
252 movements: 191 resolved by rules, 21 by AI above the 0.75 threshold (20 coded right), 40 sent to review. All 35 planted problems reached review. Entry balanced: Debe = Haber = ARS 208,316,979.70. 556 LLM calls in total, about USD 0.94 at API prices.

## Next
1. Deploy on Vercel: Root Directory `site`, framework Vite, no env vars. The domain must not contain the name of any real company.
2. Open the deployed page on phone and desktop.
3. Before making the repo public: decide on authorship lines, git history and a license (see open questions).
4. Edit the memo in `docs/memo.template.md`, then rerun `uv run ctl build`.

## Open questions
- Rate convention (official seller rate on posting date) and USDC valuation: assumptions to validate with an accountant.
- Authorship: the page subtitle and footer, `site/index.html` and `docs/README.template.md` carry the author name. Keep or remove before publishing.
- Git history: earlier commits contain the original build spec. Publishing needs either a fresh repo with one clean commit or explicit approval to rewrite history.
- No LICENSE file yet.
