# Card to Ledger AR · product memo

*Every number in this memo is filled in at build time from the prototype's data folder. None is typed by hand.*

## The problem, as a hypothesis

An Argentine company that spends in dollars with a corporate card and pays foreign contractors in USDC still keeps its books in pesos. Its month end has a last mile. Someone converts each movement at a rate they can defend, matches it to a receipt, codes it to a local chart of accounts, chases what is missing and posts one entry into a local accounting system. Global integrations sync transactions into QuickBooks, Xero or NetSuite, but they do not hand an Argentine accountant a peso entry ready to post. This comes from public information, not from customer interviews, and the first job is to test it.

## Users and jobs to be done

- **Controller or outside accountant.** Give me a peso entry I can defend, and show me only what needs my judgment.
- **CFO.** Tell me when the month is closed and what it cost in pesos.
- **Cardholder.** Tell me once what you need from me, with a link.

## What the prototype measured

A synthetic month of 252 movements and 215 receipts, scored against the correct answer for each one. Rules resolved 191 movements (75.8%). The AI resolved 21 above a confidence threshold of 0.75. A person gets 40 (15.9%), each with its evidence.

- **Account rules** were right 98.1% of the time. The 4 misses came from one broad rule that coded food delivery as travel. Rules drift too, so they need the same monthly measurement as the AI.
- **Receipt matching** paired 99.5% correctly. When two movements tie, the engine does not guess.
- **Checks** sent 35 of 35 planted problems to review.
- **AI account suggestions** for the 30 merchants no rule covers were right 90.0% of the time. At the threshold of 0.75, 24 were accepted automatically and 95.8% of those were right.
- **AI receipt reading** got all four fields right on 99.5% of receipts. Code checks every amount it reads against the charge.
- **AI explanations** passed the verifier in 44 of 44 cases. 0 fell back to a template.
- **ERP handoff.** The same entry was posted to a QuickBooks Online sandbox company through its API, 512 lines in pesos, then read back and verified to the cent. A local Argentine system would still need its own import.

## Rules, AI or a person

Rules take anything that must behave the same every month: the rate convention, receipt matching, duplicate and refund checks, and known merchants. AI takes what is open ended: receipts in any layout, the long tail of merchants, and the note a reviewer reads. People keep judgment and accountability: ties, missing evidence, low confidence and the final approval. The AI never types a number into the ledger.

## Metrics to track

1. Days to close, from month end to an approved entry.
2. Share of movements coded automatically, split by rules and AI.
3. Exceptions per hundred movements, and the trend.
4. Accuracy of automatically coded lines, audited on a sample every month.
5. Review time per exception.

## How to ship it

1. Pilot with a handful of Argentine customers and their accountants. Label one real past month together. That month becomes their test set.
2. Ship with a person reviewing everything. The AI suggests and nothing posts on its own.
3. Turn on automatic acceptance per customer only when accuracy above the threshold holds on their own labeled month. Recheck it every month.
4. Add the import file for the local system the pilot accountants use most.
5. Grow the checks and the rate conventions from what those accountants ask for.

## Eight questions for controllers

1. Which exchange rate and which date do you use for dollar card spend, and who decided it?
2. How do you value a USDC balance at month end, and has an auditor questioned it?
3. Which local system do you post into, and what file does it accept?
4. How long does the card and contractor part of the close take today, and where does the time go?
5. What happens today when a receipt is missing at close?
6. Which merchants do you always code by hand, and why?
7. What would you need to see before you trust a line coded automatically?
8. Who signs off the entry, and what evidence do they ask for?
