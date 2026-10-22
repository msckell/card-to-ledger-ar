# STATUS · Card to Ledger AR

> Rewritten at the end of each task. Last update: 2026-10-22.

## Done
- Synthetic month, deterministic close engine, Excel export, AI layer with verifier, measured threshold, page, memo and README. One command rebuilds everything: `uv run ctl build`.
- Live at https://card-to-ledger-ar.vercel.app/ (Vercel, redeploys on push to `main`).
- Page reviewed section by section with the owner. QA: every number traced to `site.json`, `noindex,nofollow`, `robots.txt`, `X-Robots-Tag`. Closing LinkedIn button opens in a new tab.
- **USDC at the crypto rate (2026-10-22).** USDC payouts, top ups, opening balance and month end remeasurement use the crypto dollar seller rate from the snapshot (`fx.usdc_series: cripto`). Dollar card spend stays at the official rate. Paying the card with USDC sends the gap to exchange differences. Test in `tests/test_engine.py`.
- **QuickBooks Online sandbox handoff (2026-10-22).** `uv run ctl qbo-auth` refreshes the OAuth token (rotated token saved back to `.env`) and shows the company. `uv run ctl qbo-post` posts `CTL-2026-09` once (DocNumber checked first), in ARS with multicurrency on, 512 lines from `close.json`, then reads it back and verifies every line, the 15 accounts and both totals to the cent. Result in `data/out/qbo_post.json` (no tokens, no realm ID). Mapping in `config/quickbooks_accounts.yaml`. Sandbox only, never in `ctl build` or CI. Page strip in the journal section, README step and run commands, memo line. Offline tests with a fake sandbox in `tests/test_qbo.py`.

## Results (data/eval.json, data/out/qbo_post.json)
252 movements: 191 by rules, 21 by AI above 0.75, 40 to review. Entry balanced at ARS 208,889,403.18. In QuickBooks (entry reposted after the rate change): 512 lines, 7 of 7 checks passed.

## Next
1. Make the repo public when ready.
2. Edit the memo in `docs/memo.template.md`, then rerun `uv run ctl build`.

## Open questions
- Rate convention (official for card spend, crypto for USDC): assumption to validate with an accountant.
- QuickBooks stores the entry rate with 7 decimals (0.0006472 USD per ARS). It only moves the sandbox's own USD column, which is not checked.
- The Intuit refresh token lives in `.env`. If it expires, get a new one from the OAuth 2.0 Playground.
