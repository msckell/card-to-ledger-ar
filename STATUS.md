# STATUS · Card to Ledger AR

> Rewritten at each checkpoint. Last update: 2026-10-21, end of Phase 3 (before the FINAL CHECKPOINT).

## Done
- Phase 1 · data and engine. Phase 2 · AI layer and eval. Phase 3 · page, memo, README.
- One command rebuilds everything: `uv run ctl build` (AI outputs cached in `data/ai/`, 0 new calls when nothing changed).
- Page in `site/` builds clean (`npx tsc -b && npx vite build`). Checked on desktop and at 375 px: no horizontal scroll.
- QA done: every number on the page traced to `data/site/site.json`. Excel and the receipt PDFs in the queue are served. `noindex,nofollow` meta, `robots.txt` disallows all, `X-Robots-Tag` header in `site/vercel.json`. No wording about Jeeves internals or customers. Secret scan over the full git history: clean, no `.env` tracked.
- Private repo: https://github.com/msckell/card-to-ledger-ar

## Results (data/eval.json)
De 252 movimientos, 191 los resolvieron las reglas, 21 la IA (20 bien codificados) y 40 van a revisión. Umbral recomendado 0.75. Las 35 anomalías plantadas llegaron a revisión. Asiento balanceado: Debe = Haber = ARS 208,316,979.70. LLM: 556 llamadas en total, unos USD 0.94 a precio de API, sobre la suscripción de Claude.

## Pending for Maxi (cannot be done without him)
1. **Vercel**: Add New Project → import `msckell/card-to-ledger-ar` → Root Directory `site` → framework Vite → Deploy. No env vars. Name the project `card-to-ledger-ar` (the domain must not contain "jeeves").
2. **FINAL CHECKPOINT**: open the deployed page on phone and desktop. Local preview: `cd site && npx vite preview`.
3. **Repo public or not**: secret scan is clean. Before making it public, reread `CLAUDE.md` (it describes the job application) and decide if it stays in the repo. Then set `REPO_URL` in `site/src/App.tsx` so the page links to it.
4. **Memo**: `docs/memo.template.md` is a draft to edit. Rerun `uv run ctl build` after editing, it fills the numbers.

## Open questions
- Rate convention (official seller rate on posting date) and USDC valuation: assumptions to validate with an accountant.
- Disk C: was full during the build. `site/node_modules` is a junction to `D:\card-to-ledger-ar-build\node_modules`. Running `npm install` inside `site/` replaces it with a real folder on C:.
