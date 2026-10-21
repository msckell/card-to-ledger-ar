import { site } from './data'
import { Badge, Stat } from './ui'

export default function Overview() {
  const s = site.summary
  const total = s.transactions
  const parts = [
    { key: 'rules', label: 'Rules', n: s.split.rules, color: 'bg-rules' },
    { key: 'ai', label: 'AI, above the threshold', n: s.split.ai, color: 'bg-ai' },
    { key: 'review', label: 'A person', n: s.split.review, color: 'bg-review' },
  ]
  return (
    <div id="overview" className="pb-12 pt-10 sm:pb-16 sm:pt-16">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="review">Fictional company, synthetic data</Badge>
        <Badge>Close of {site.meta.period_label}</Badge>
      </div>
      <h1 className="mt-5 font-serif text-4xl font-semibold leading-tight sm:text-5xl">{site.meta.title}</h1>
      <p className="mt-2 text-base text-muted">{site.meta.subtitle}</p>

      <div className="mt-8 max-w-2xl space-y-3 text-[16px] leading-relaxed">
        <p>
          An Argentine company spends in dollars with a corporate card and pays contractors abroad in USDC, but it
          keeps its books in pesos.
        </p>
        <p>
          Every month its accountant converts each movement at the right rate, finds its receipt, picks the account,
          chases what is missing and types a journal entry into a local system.
        </p>
        <p>
          Global accounting integrations stop before that last mile. This prototype shows that close arriving ready to
          review, with every split between rules, AI and people measured against known correct answers.
        </p>
        <p className="text-sm text-faint">The problem is a hypothesis to validate with controllers, not a finding.</p>
      </div>

      <div className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-3">
        <Stat label="Movements in the month" value={total} sub={`${s.receipts} receipts and invoices`} />
        <Stat wide label="Spend in USD" value={`USD ${s.spend_usd}`} sub={`Card ${s.card_net_usd} · USDC ${s.payouts_usdc}`} />
        <Stat wide label="Spend in ARS" value={`ARS ${s.spend_ars}`} sub="At the official rate of each day" />
        <Stat label="Resolved by rules" value={s.split.rules} tone="rules" />
        <Stat label="Accepted from AI" value={s.split.ai} tone="ai" sub={s.threshold ? `Confidence at or above ${s.threshold}` : 'AI not run'} />
        <Stat label="Sent to a person" value={s.split.review} tone="review" sub={`${s.exceptions} open exceptions`} />
      </div>

      <div className="mt-6">
        <div className="flex h-3 w-full overflow-hidden rounded-full bg-line" role="img" aria-label="Share of movements by who resolved them">
          {parts.map((p) => (
            <div key={p.key} className={p.color} style={{ width: `${(p.n / total) * 100}%` }} />
          ))}
        </div>
        <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted">
          {parts.map((p) => (
            <span key={p.key} className="inline-flex items-center gap-1.5">
              <span className={`inline-block h-2 w-2 rounded-full ${p.color}`} />
              {p.label} <span className="num text-ink">{p.n}</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
