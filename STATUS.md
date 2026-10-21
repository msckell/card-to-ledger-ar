# STATUS · Card to Ledger AR

> Rewritten at each checkpoint. Last update: 2026-10-21, end of Phase 2 (CHECKPOINT B).

## Done
- Phase 1 · data and engine (see git log). 252 movements, 215 receipts, balanced ARS entry, Excel.
- Phase 2 · AI layer and measurement. `uv run ctl build` runs everything in order, AI outputs cached in `data/ai/`.
  - Receipt reading: Claude Haiku 5.5. Account suggestions and explanations: Claude Sonnet 5.5.
  - Backend: `claude -p` on the Claude subscription (no API key needed). The SDK path is used if `ANTHROPIC_API_KEY` is set.
  - Verifier with 9 tests. 23 tests green, ruff clean.
- Phase 3 page code in `site/` builds. Memo and README are rendered from templates with values from `data/`.

## Checkpoint B (from data/eval.json)
De 252 movimientos, 191 los resolvieron las reglas, 21 la IA (24 sugerencias pasaron el umbral 0.75 con 95.8% de acierto, 3 igual fueron a revisión por falta de comprobante) y 40 van a revisión.
- AI account suggestions: 27 of 30 right overall (90.0%). Recommended threshold 0.75 (lowest that reaches 95% with at least 5 accepted).
- AI receipt reading: 99.5% all four fields. Prompt v2: v1 left the currency empty on restaurant tickets that print none. Both runs are counted in usage.
- Explanations: 44 of 44 passed the verifier (40 first try, 4 after a retry for raw figures).
- LLM usage: 556 calls in total across every run, about USD 0.94 at API prices.

## Next
- Phase 3: visual QA of the page, QA checklist, commit.
- Deploy: needs Maxi (see below).

## Manual steps for Maxi
1. API key: not needed (the build ran on the Claude subscription, same as wFIAT).
2. Vercel: import `msckell/card-to-ledger-ar`, Root Directory `site`, framework Vite. No env vars needed.
3. Decide whether the repo goes public (secret scan done before).

## Open questions
- Rate convention (official seller rate on posting date) and USDC valuation are assumptions to validate with an accountant.
- Disk C: was full during the build. `site/node_modules` is a junction to `D:\card-to-ledger-ar-build\node_modules`. Running `npm install` inside `site/` replaces the junction with a real folder on C:.
