# CLAUDE.md · Card to Ledger AR (independent prototype)

> Startup doc. Any AI session in this repo reads this FIRST, then `STATUS.md`.
> Owner: Máximo Sckell (Maxi). Created 2026-10-21. Goal: build the whole thing end to end in ONE Claude Code session.

---

## 0. How we work

- Maxi talks to you in **Spanish (rioplatense)**. Answer in Spanish, in plain words, and explain any jargon in one simple sentence.
- Code, comments, commits, README, page and memo: **English**. Accounting labels that an Argentine accountant reads (chart of accounts, journal entry columns, Excel sheet names) stay in **Spanish**.
- Prose written in Maxi's name (page, README, memo) uses **no dashes and no semicolons**.
- Maxi does not review diffs. There are 3 short **CHECKPOINTS**. At each one, show him something he can look at (a table, a file, a page), wait for his OK, then continue. Keep each checkpoint under 2 minutes of his time.
- Commit at the end of each phase. Rewrite `STATUS.md` (one screen: done, next, open questions) at each checkpoint so a fresh session could continue.
- **Before writing code, tell Maxi in 5 lines how you will build it and how long each phase should take.**

---

## 1. Context

This repo is Maxi's independent prototype for the **Product Manager, Accounting** role at **Jeeves** (remote, Argentina).

Jeeves is a stablecoin-native banking platform for global enterprises: corporate cards, accounts payable, treasury payments and spend management on one platform. It launched in Argentina in July 2026. Its public materials say AI agents already handle reconciliation and financial automation.

The role asks the PM to ship improvements to the accounting experience (spend data, reconciliation, compliance, audit trails), to **identify and validate AI automation opportunities and know when AI fits versus when deterministic rules are required**, to drive ERP integrations, and to run discovery with controllers and CFOs.

**The problem this prototype addresses (a hypothesis, say so on the page):**
An Argentine company spends in USD with a corporate card and pays foreign contractors in USDC, but keeps its books in pesos. Every month its accountant must convert each movement to ARS at the right exchange rate, match each one to its receipt, assign it to the chart of accounts, chase what is missing and post a journal entry into a local accounting system. Global integrations (QuickBooks, Xero, NetSuite) do not cover that last mile.

**What the prototype proves:** a month end close for that company, ready to review, where deterministic rules do everything they can, AI only handles what rules cannot, a person reviews the rest, and **every split is measured against known correct answers**. That measured split is the answer to the central question of the job post.

---

## 2. Readers and success

- **Reader 1, non technical, 30 seconds:** understands the problem, sees a finished close and sees that it is reliable.
- **Reader 2, product and engineering leads:** sees product judgment (what to automate, how to measure it, what to ship first) and clean engineering.

Success means a public page, no login, no API key, that shows:
1. The close for September 2026 of the fictional company: totals, how many items were resolved by rules, by AI and by a person.
2. The review queue a controller would work through, each item with its evidence and a plain explanation.
3. The journal entry in ARS, balanced, downloadable as Excel.
4. **"Rules or AI?"**: the measured accuracy of each step and a confidence threshold chart showing the trade off between automation and accuracy.
5. A short product memo.

---

## 3. Decisions (do not re-litigate)

1. **Synthetic data, clearly labeled.** A fictional company, "Andes Labs SRL", an Argentine SaaS company with about 40 people. Never imply it is a real customer. Never imply this is how Jeeves works internally.
2. **The transaction export schema is invented** (Jeeves has no public API documentation we could find). Label it "assumed export format" on the page.
3. **Ground truth exists for everything.** The data generator writes the correct answer for every transaction (account, matching receipt, anomaly type). Evaluation compares against it.
4. **Numbers come only from deterministic code.** The LLM never types a figure. Templates render every number and status. A verifier rejects any LLM text containing raw figures (same pattern as Maxi's wFIAT project).
5. **Decimal and integer cents only.** Never float. Round only when displaying.
6. **Exchange rates are real and cited.** Use official historical USD/ARS rates from a free public source (try ArgentinaDatos or the BCRA public API). Save a snapshot CSV with source URL and download date, and read from the snapshot so the build is reproducible. The rate convention (which rate, which day) is a config value labeled **"assumption, to validate with an accountant"**. Default: official seller rate on the transaction date.
7. **Taxes are out of scope.** No VAT, no withholdings, no perceptions. The page says so explicitly.
8. **AI only in three places:** reading receipts, suggesting an account when no rule applies, explaining exceptions. Each one is measured.
9. **Static site plus JSON produced by the pipeline.** No backend, no database, no live LLM on the page. All LLM calls happen at build time and their outputs are committed.
10. **Not branded.** No Jeeves logo, colors or name in the product title. Title: "Card to Ledger AR" (working name). Subtitle: "Independent prototype for Jeeves by Máximo Sckell". `noindex,nofollow` meta tag and a `robots.txt` that disallows everything. The domain must not contain "jeeves".
11. **Repo private while building.** It becomes public only if Maxi decides, after a secret scan.

**Stack**
- Pipeline: Python 3.12 with uv. Dependencies minimal: httpx, pyyaml, pydantic, openpyxl, reportlab (receipt PDFs), pypdf, anthropic, pytest, ruff.
- LLM: Anthropic Python SDK, model from env `ANTHROPIC_MODEL` (check the current Anthropic docs for the right model string). Use structured outputs. Keep total LLM cost under USD 2 and print the count of calls.
- Site: Vite + React + TypeScript + Tailwind, reads static JSON. Recharts for the threshold chart.
- Hosting: Vercel.
- Secrets in `.env` (gitignored) and `.env.example`.

---

## 4. The data (generator spec)

`pipeline/generate.py`, seeded, deterministic, one command.

**Month:** September 2026. About 250 transactions.

**Transaction mix**
- Card spend in USD: ads (Meta, Google), cloud (AWS, GCP), software (Google Workspace, Slack, Figma, Notion, GitHub, LLM APIs), travel (flights, hotels, Uber), meals, conferences.
- USDC payouts to foreign contractors.
- ARS pay ins (top ups), refunds, card fees.
- Use generic or fictional merchant strings that look like real card descriptors (for example "AWS EMEA", "FACEBK *ADS"). Real vendor names as merchants are fine, they are not endorsements.

**Receipts:** PDFs generated with 3 or 4 different layouts, in English and Spanish, so extraction is not trivial.

**Planted anomalies (with ground truth labels):**
- Missing receipt: about 8%
- Duplicate charge: about 2%
- Receipt amount differs from charge (tip, partial refund, currency confusion): about 3%
- Ambiguous merchant that no rule covers: about 12% (these go to AI)
- Refund that must offset its original charge: a few

**Chart of accounts:** a short Argentine style plan in Spanish (for example Publicidad y marketing, Servicios de nube, Licencias de software, Honorarios de contratistas del exterior, Viajes y viáticos, Comidas y representación, Comisiones y gastos bancarios, Diferencias de cambio, Tarjeta corporativa a pagar, Cuenta USDC). About 15 accounts. Keep it in `config/chart_of_accounts.yaml`.

**Rules:** `config/rules.yaml` maps merchant patterns to accounts. Rules must cover most but deliberately not all transactions.

---

## 5. Phases and checkpoints

### Phase 1 · Data and engine (target 2 h)
1. Repo skeleton, uv, `.env.example`, `git init`, first commit.
2. FX snapshot from the public source. If the source fails, stop and tell Maxi. Never invent rates.
3. Data generator with ground truth.
4. Deterministic engine:
   - FX conversion per transaction (Decimal, cents).
   - Receipt matching by amount, date window and merchant similarity.
   - Duplicate, missing receipt, amount mismatch and refund detection.
   - Rule based account assignment.
   - Monthly journal entry in ARS, with a hard check that debits equal credits.
   - Audit trail per line: rule ID or AI suggestion ID, status, who approved (simulated as "pending review" for human items).
5. Excel export with sheets **Resumen · Asiento · Movimientos · Excepciones · Metodología**. Metodología lists every assumption labeled **documented**, **assumption** or **out of scope**.
6. pytest: balance check, FX conversion, duplicate detection, refund offset.

**CHECKPOINT A.** Show Maxi in a small table: transaction count, totals in USD and ARS, how many resolved by rules, how many left for AI, anomalies found versus planted. He opens the Excel.

### Phase 2 · AI layer and measurement (target 1 h 30)
1. `ai/extract.py`: read each receipt PDF and return vendor, date, amount, currency with structured output. Code checks the extracted amount against the transaction. Mismatch becomes an exception, never a silent fix.
2. `ai/suggest.py`: for transactions no rule covers, suggest one account **from the allowed list only** (enum), with a short reason and a confidence from 0 to 1. Show only the transaction facts, never the ground truth.
3. `ai/explain.py`: one plain English explanation per exception, citing facts by ID, rendered by templates. Verifier rejects raw figures, invented IDs and claims like "approved" or "compliant". Retry with feedback up to 2 times, then fall back to the template only. Log every attempt.
4. `eval.py` compares against ground truth and writes `data/eval.json`:
   - Extraction accuracy per field.
   - Account accuracy for rules and for AI separately.
   - Final split: resolved by rules, accepted from AI, sent to a person.
   - **Threshold sweep:** for confidence thresholds from 0.5 to 0.95, the share of AI suggestions auto accepted and their accuracy. Pick a recommended threshold and say why.
5. pytest for the verifier (at least 6 cases: raw figure, invented ID, banned claim must fail, clean explanation and paraphrase must pass).

**CHECKPOINT B.** Show Maxi the eval table and the recommended threshold, in plain Spanish: "de 250 movimientos, X los resolvieron las reglas, Y la IA con Z% de acierto, W van a revisión".

### Phase 3 · Page, memo and deploy (target 2 h)
**Page views (mobile first, clean, light theme, no Jeeves branding):**
1. **Overview.** Title, subtitle, the problem in three plain sentences, the close summary as cards (transactions, USD total, ARS total, resolved by rules, by AI, sent to review), a "fictional company, synthetic data" badge.
2. **Review queue.** Each exception with transaction, receipt evidence, AI suggestion and confidence when relevant, plain explanation, status.
3. **Journal entry.** Debe and Haber in ARS, the balance check visible, Excel download.
4. **Rules or AI?** Accuracy per step, the threshold chart, and a decision table: step, handled by, why, measured accuracy.
5. **How it works.** Simple diagram: export and receipts → rules → AI (three uses) → verifier → review queue → journal entry. Methodology labels. Link to the repo if Maxi makes it public.
6. **Product memo.** Rendered from `docs/memo.md`.

**Product memo (`docs/memo.md`, 1 to 2 pages, English).** Draft it, Maxi edits:
- The problem for an Argentine controller using a USD card (labeled hypothesis).
- Users and jobs to be done.
- What to automate with rules, what with AI, what stays human, with the measured numbers from `eval.json`.
- Metrics to track: days to close, share auto coded, exception rate, accuracy, review time.
- How to ship it: small pilot, human review first, raise automation as accuracy proves out.
- 8 discovery questions to ask controllers.
- Every number in the memo comes from `data/`. None is invented.

**Rules for the page:** every number read from `data/`, none hardcoded. Footer: Máximo Sckell · linkedin.com/in/msckell · github.com/msckell. Disclaimer: "Independent prototype. Not affiliated with Jeeves. Fictional company and synthetic transactions. Exchange rates from a public source. Taxes out of scope."

**Deploy to Vercel** (project name for example `card-to-ledger-ar`). Maxi links the repo when you tell him.

**README** in English: what and why, how it works, results from `eval.json`, assumptions, how to run, limitations.

**FINAL CHECKPOINT.** Maxi opens the page on his phone and on desktop. QA before that:
- trace every number on the page back to `data/`
- check every link and the Excel download
- confirm noindex and robots.txt
- confirm no wording claims anything about Jeeves internals or real customers
- secret scan over the git history

---

## 6. Rules

- Never invent data. A failed source is never a zero. If something blocks you for more than 20 minutes, stop and explain in Spanish what you tried.
- Keep the conversation light. Scripts write raw data to files and print short summaries only.
- Never commit secrets. No destructive git operations without Maxi's OK.

## 7. Manual steps for Maxi (tell him when each is due)
1. Phase 2: `ANTHROPIC_API_KEY` in `.env` (the same one used for wFIAT works).
2. Phase 3: link the repo to Vercel.
3. End: decide whether the repo goes public.
