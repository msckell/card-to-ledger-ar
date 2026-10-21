import type { ReactNode } from 'react'
import { site } from './data'
import { Badge, Eyebrow, Section } from './ui'

const CHORES: { title: string; body: string; icon: ReactNode }[] = [
  { title: 'Convert', body: 'Each movement to pesos, at a rate they can defend', icon: <path d="M4 8h12l-3-3M16 12H4l3 3" /> },
  { title: 'Match', body: 'Each charge to its receipt, in English or Spanish', icon: <path d="M5 4h7l3 3v9H5zM12 4v3h3M8 11l1.5 1.5L12.5 9" /> },
  { title: 'Code', body: 'Each one to the local chart of accounts', icon: <path d="M4 6h12M4 10h8M4 14h10" /> },
  { title: 'Chase', body: 'Missing receipts, duplicates and odd amounts', icon: <path d="M9 4a5 5 0 1 0 0 10A5 5 0 0 0 9 4zM13 13l3.5 3.5" /> },
  { title: 'Post', body: 'One entry, typed into a local accounting system', icon: <path d="M4 15h12M6 15V9M10 15V5M14 15v-4" /> },
]

export default function Problem() {
  const t = site.summary.by_type
  const card = (t.card_purchase ?? 0) + (t.card_fee ?? 0) + (t.card_refund ?? 0)
  const preview = [
    ...site.journal.rows.filter((r) => r.account.startsWith('5.1.') && r.debe).slice(0, 3),
    ...site.journal.rows.filter((r) => r.account === '2.1.01'),
  ]
  return (
    <Section
      id="problem"
      eyebrow="The problem"
      title="Global integrations stop one step before a peso ledger."
      intro={
        <>
          An Argentine company spends in dollars, but its books are in pesos. Every month someone does five chores by
          hand before the close is done. <Badge tone="neutral">Hypothesis to validate with controllers</Badge>
        </>
      }
    >
      <div className="grid items-stretch gap-4 lg:grid-cols-[1fr_auto_1.1fr_auto_1fr]">
        {/* What arrives */}
        <div className="rounded-2xl border border-line bg-paper p-5">
          <Eyebrow>What arrives, in dollars</Eyebrow>
          <ul className="mt-4 space-y-3">
            <Input label="Card charges, fees and refunds" n={card} unit="USD" />
            <Input label="Payouts to contractors abroad" n={t.usdc_payout ?? 0} unit="USDC" />
            <Input label="Receipts and invoices, not linked to anything" n={site.summary.receipts} unit="PDF" />
          </ul>
        </div>

        <Connector />

        {/* The manual work */}
        <div className="rounded-2xl border border-line p-5">
          <Eyebrow>What someone does by hand</Eyebrow>
          <ol className="mt-4 space-y-3">
            {CHORES.map((c, i) => (
              <li key={c.title} className="flex items-center gap-3">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-night text-gold">
                  <svg viewBox="0 0 20 20" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                    {c.icon}
                  </svg>
                </span>
                <span>
                  <span className="block text-sm font-semibold">
                    <span className="num text-faint">{i + 1}.</span> {c.title}
                  </span>
                  <span className="block text-xs leading-relaxed text-muted">{c.body}</span>
                </span>
              </li>
            ))}
          </ol>
        </div>

        <Connector />

        {/* What the books need */}
        <div className="rounded-2xl bg-night p-5 text-on-night">
          <Eyebrow night>What the books need, in pesos</Eyebrow>
          <div className="mt-4 overflow-hidden rounded-xl border border-night-line text-xs">
            <div className="grid grid-cols-[1fr_auto_auto] gap-3 border-b border-night-line px-3 py-2 text-on-night-muted">
              <span>Cuenta</span>
              <span className="text-right">Debe</span>
              <span className="text-right">Haber</span>
            </div>
            {preview.map((r) => (
              <div key={r.account} className="grid grid-cols-[1fr_auto_auto] gap-3 border-b border-night-line px-3 py-2 last:border-0">
                <span className="truncate">{r.name}</span>
                <span className="num text-right">{r.debe ? '●' : ''}</span>
                <span className="num text-right">{r.haber ? '●' : ''}</span>
              </div>
            ))}
          </div>
          <p className="mt-3 text-xs text-on-night-muted">
            One balanced entry in ARS, with an audit trail per line.
          </p>
        </div>
      </div>
    </Section>
  )
}

function Input({ label, n, unit }: { label: string; n: number; unit: string }) {
  return (
    <li className="flex items-center justify-between gap-3 rounded-xl bg-card px-3 py-2.5 ring-1 ring-line">
      <span className="text-sm leading-snug">{label}</span>
      <span className="shrink-0 text-right">
        <span className="num block text-lg font-semibold">{n}</span>
        <span className="block text-[10px] font-semibold tracking-wider text-faint">{unit}</span>
      </span>
    </li>
  )
}

function Connector() {
  return (
    <div className="flex items-center justify-center text-gold" aria-hidden>
      <svg viewBox="0 0 24 24" className="h-6 w-6 rotate-90 lg:rotate-0" fill="none" stroke="currentColor" strokeWidth="1.6">
        <path d="M4 12h16M14 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  )
}
