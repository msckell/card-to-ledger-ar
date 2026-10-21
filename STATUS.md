# STATUS · Card to Ledger AR

> Rewritten at each checkpoint. Last update: 2026-10-21, end of Phase 1 (CHECKPOINT A).

## Done
- Phase 1 · data and engine. `uv run ctl fx` (rate snapshot) · `uv run ctl generate` · `uv run ctl close`.
- FX: ArgentinaDatos official and crypto series, frozen in `data/fx/` with `source.json`.
- 252 synthetic movements, 215 receipt PDFs in 4 layouts (EN and ES), ground truth in `data/truth/`.
- Engine: rules, receipt matching, duplicates, missing receipts, amount mismatches, refunds, journal in ARS with month end remeasurement, balance check, audit trail per line.
- Excel `data/out/cierre_2026-09_andes_labs.xlsx` (Resumen, Asiento, Movimientos, Excepciones, Metodología).
- 14 tests green, ruff clean.

## Checkpoint A numbers (template receipt reader, before AI)
| | |
|---|---|
| Movements | 252 |
| Net spend | USD 132,274.72 = ARS 203,535,812.05 |
| Resolved by rules | 191 |
| Left for AI (no rule) | 30 |
| Sent to review | 61 (30 of them only because AI has not run yet) |
| Planted anomalies caught in review | 35 of 35 |
| Entry | Debe = Haber = ARS 208,316,979.70 |

## Next
- Phase 2: AI reading of receipts, account suggestions, explanations, eval and threshold.

## Open questions for Maxi
- Rate convention (official seller rate on posting date) is an assumption to validate with an accountant.
- Maxi was away during the build: checkpoints were not reviewed live. Review them on the final page.
