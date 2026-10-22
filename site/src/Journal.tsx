import { site } from './data'
import { Arrow, ButtonLink, Check, Section } from './ui'

const SHEETS = ['Summary', 'Entry', 'Movements', 'Exceptions', 'Methodology']

export default function Journal() {
  const j = site.journal
  return (
    <Section
      id="journal"
      tone="paper"
      eyebrow="The deliverable"
      title={`The ${site.meta.period_label} entry, in pesos, ready to post.`}
      intro={
        <>
          One summary entry built from {j.lines} audited lines. Each movement is valued at the official seller rate of its
          posting day. The USDC account and the card payable are remeasured at the closing rate of{' '}
          {site.summary.closing_rate}. Items still in review sit in a suspense account until a person decides.
        </>
      }
    >
      <div className="grid gap-5 lg:grid-cols-[1.6fr_1fr]">
        <div className="overflow-hidden rounded-3xl border border-line bg-card">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-paper text-left text-[11px] uppercase tracking-[0.14em] text-faint">
                <th className="px-4 py-3 font-semibold sm:px-6">Account</th>
                <th className="hidden px-3 py-3 text-right font-semibold sm:table-cell">Debit</th>
                <th className="hidden px-4 py-3 text-right font-semibold sm:table-cell sm:px-6">Credit</th>
              </tr>
            </thead>
            {j.groups.map((g) => (
              <tbody key={g.name} className="border-b border-line">
                <tr className="bg-paper/60">
                  <td colSpan={3} className="px-4 pb-1.5 pt-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-gold-text sm:px-6">
                    {g.name}
                  </td>
                </tr>
                {j.rows
                  .filter((r) => g.accounts.includes(r.account))
                  .map((r) => (
                    <tr key={r.account} className="border-t border-line/60">
                      <td className="px-4 py-2.5 sm:px-6">
                        <span className="block leading-snug">{r.name}</span>
                        <span className="font-mono text-[11px] text-faint">{r.account}</span>
                        <span className="num mt-0.5 block text-[13px] sm:hidden">
                          {r.debe ? <>Debit {r.debe}</> : <span className="text-muted">Credit {r.haber}</span>}
                        </span>
                      </td>
                      <td className="num hidden px-3 py-2.5 text-right align-top sm:table-cell">{r.debe}</td>
                      <td className="num hidden px-4 py-2.5 text-right align-top sm:table-cell sm:px-6">{r.haber}</td>
                    </tr>
                  ))}
                <tr className="border-t border-line font-semibold">
                  <td className="px-4 py-2.5 text-sm sm:px-6">
                    Subtotal
                    <span className="num block text-[13px] font-medium text-muted sm:hidden">
                      {g.debe && <>Debit {g.debe}</>}
                      {g.debe && g.haber && ' · '}
                      {g.haber && <>Credit {g.haber}</>}
                    </span>
                  </td>
                  <td className="num hidden px-3 py-2.5 text-right sm:table-cell">{g.debe}</td>
                  <td className="num hidden px-4 py-2.5 text-right sm:table-cell sm:px-6">{g.haber}</td>
                </tr>
              </tbody>
            ))}
            <tfoot>
              <tr className="bg-night font-semibold text-on-night">
                <td className="px-4 py-3.5 sm:px-6">
                  Totals, ARS
                  <span className="num block text-[13px] font-medium text-gold-light sm:hidden">
                    Debit {j.totals.debe} · Credit {j.totals.haber}
                  </span>
                </td>
                <td className="num hidden px-3 py-3.5 text-right text-gold-light sm:table-cell">{j.totals.debe}</td>
                <td className="num hidden px-4 py-3.5 text-right text-gold-light sm:table-cell sm:px-6">{j.totals.haber}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div className="flex flex-col gap-5 lg:sticky lg:top-24 lg:self-start">
          <div className="rounded-3xl border border-line bg-card p-6">
            <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-gold-text">
              <Check className="h-4 w-4" /> {j.totals.balanced ? 'Balanced to the cent' : 'Not balanced'}
            </p>
            <div className="mt-4 space-y-1">
              <p className="text-xs text-faint">Debits</p>
              <p className="num text-2xl font-semibold">ARS {j.totals.debe}</p>
              <p className="py-1 text-xl font-semibold text-gold-text" aria-hidden>
                =
              </p>
              <p className="text-xs text-faint">Credits</p>
              <p className="num text-2xl font-semibold">ARS {j.totals.haber}</p>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-muted">
              The build stops if debits and credits differ by a single cent. Every line keeps its audit trail: the rule or AI
              suggestion behind it, its status, and who approved it.
            </p>
          </div>

          <div className="rounded-3xl bg-night p-6 text-on-night">
            <p className="text-lg font-semibold">The whole close, in one Excel file</p>
            <p className="mt-1 text-xs text-on-night-muted">Labels in Spanish inside the file, the way a local accountant reads them.</p>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {SHEETS.map((s) => (
                <span key={s} className="rounded-md bg-night-2 px-2 py-1 text-xs text-on-night-muted ring-1 ring-night-line">
                  {s}
                </span>
              ))}
            </div>
            <div className="mt-5">
              <ButtonLink href={j.excel} download>
                Download the Excel <Arrow className="rotate-90" />
              </ButtonLink>
            </div>
          </div>
        </div>
      </div>
      <QuickBooksStrip />
    </Section>
  )
}

function QuickBooksStrip() {
  const q = site.quickbooks
  if (!q) return null
  const passed = q.result === 'pass'
  const facts = [
    { label: 'Entry number', value: q.doc_number },
    { label: 'Lines posted', value: String(q.lines) },
    { label: 'Accounts matched', value: `${q.accounts_matched} of ${q.accounts}` },
    { label: 'Checks passed', value: `${q.checks_passed} of ${q.checks_total}` },
  ]
  return (
    <div className="mt-5 overflow-hidden rounded-3xl border border-line bg-card">
      <div className="grid gap-6 p-6 sm:p-8 lg:grid-cols-[1fr_1.15fr] lg:items-center">
        <div>
          <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-gold-text">
            <Check className="h-4 w-4" /> QuickBooks Online sandbox company
          </p>
          <p className="mt-3 text-xl font-semibold leading-snug">
            {passed
              ? 'Posted to a QuickBooks Online sandbox company through the API. Read back and verified to the cent.'
              : 'Posted to a QuickBooks Online sandbox company through the API. The read back did not match.'}
          </p>
          <dl className="mt-5 grid grid-cols-2 gap-x-4 gap-y-3">
            {facts.map((f) => (
              <div key={f.label}>
                <dt className="text-xs text-faint">{f.label}</dt>
                <dd className="num text-lg font-semibold">{f.value}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-5 text-sm leading-relaxed text-muted">
            The same {q.lines} lines in {q.currency} went in through the Intuit Accounting API on {q.posted_at}. The command
            reads the entry back and compares every line, each account and the totals with this close. Debits and credits
            in QuickBooks are ARS {q.entry_total} once each account is netted. It never posts the same entry twice. The
            sandbox keeps its books in {q.home_currency} and shows a {q.home_currency} column of its own, which is not
            checked. In real use a controller approves the close before this step.
          </p>
        </div>
        {q.screenshot && (
          <figure className="min-w-0">
            <a href={q.screenshot} target="_blank" rel="noreferrer" className="block overflow-hidden rounded-xl border border-line">
              <img
                src={q.screenshot}
                alt={`Journal entry ${q.doc_number} open in the QuickBooks Online sandbox company, dated 30 September 2026, with its first lines: account, debit, credit and a description that starts with the journal line ID.`}
                className="block h-auto w-full"
                loading="lazy"
              />
            </a>
            <figcaption className="mt-2 text-xs leading-relaxed text-faint">
              Screenshot of the sandbox. QuickBooks prints the peso amounts with the $ sign. The entry currency is{' '}
              {q.currency}.
            </figcaption>
          </figure>
        )}
      </div>
    </div>
  )
}
