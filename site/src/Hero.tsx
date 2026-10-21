import type { ReactNode } from 'react'
import { pct, site } from './data'
import { Arrow, Badge, ButtonLink, Dot, GoldRule, WHO, type Who } from './ui'

const DOES: { title: string; body: string; icon: ReactNode }[] = [
  {
    title: 'Reads',
    body: 'Every card charge, USDC payout and receipt of the month.',
    icon: <path d="M5 3h7l3 3v11H5zM12 3v3h3M8 10h4M8 13h4" />,
  },
  {
    title: 'Resolves',
    body: 'Converts, matches and codes each one with rules, and AI where rules stop.',
    icon: <path d="M4 6h12M4 10h12M4 14h7M14 13l1.5 1.5L18 12" />,
  },
  {
    title: 'Delivers',
    body: 'A balanced journal entry in pesos and a short review queue for a person.',
    icon: <path d="M4 4h12v12H4zM4 8h12M9 8v8" />,
  },
]

export default function Hero() {
  const s = site.summary
  const e = site.eval
  const total = s.transactions
  const parts: { who: Who; n: number; label: string }[] = [
    { who: 'rules', n: s.split.rules, label: 'Resolved by rules' },
    { who: 'ai', n: s.split.ai, label: 'Resolved by AI' },
    { who: 'review', n: s.split.review, label: 'Sent to a person' },
  ]
  const planted = Object.values(e.anomalies).reduce((a, v) => a + v.planted, 0)
  const caught = Object.values(e.anomalies).reduce((a, v) => a + v.caught_in_review, 0)
  const rec = e.threshold.recommended_row
  const usage = e.llm_usage

  const found: { value: string; label: string }[] = [
    { value: s.no_touch_share, label: `of movements posted with no human touch, ${s.no_touch} of ${total}` },
    { value: `${caught} of ${planted}`, label: 'planted problems caught before posting' },
    { value: pct(e.extraction.ai?.all_fields), label: 'of receipts read right by AI, all four fields' },
    {
      value: rec ? pct(rec.accuracy) : 'n/a',
      label: rec ? `of AI coded accounts right at the ${e.threshold.recommended} threshold` : 'AI not run',
    },
    { value: `ARS ${site.journal.totals.difference}`, label: 'difference between debits and credits' },
    {
      value: usage ? `USD ${usage.total_cost_usd.toFixed(2)}` : 'n/a',
      label: usage ? `in AI cost for the whole month, ${usage.total_calls} calls` : 'AI not run',
    },
  ]

  return (
    <section id="top" className="relative overflow-hidden bg-night text-on-night">
      <Curves />
      <div className="relative mx-auto max-w-6xl px-4 pb-16 pt-10 sm:px-6 sm:pb-24 sm:pt-14">
        {/* Who made it, and for whom */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <p className="text-sm sm:text-base">
            <span className="font-semibold text-gold-light">{site.meta.author}</span>
            <span className="text-on-night-muted"> · {site.meta.subtitle}</span>
          </p>
          <Badge tone="night">Fictional company · synthetic data</Badge>
        </div>

        <div className="mt-10 grid items-center gap-14 lg:grid-cols-[1.05fr_1fr] lg:gap-12">
          <div>
            <GoldRule />
            <p className="mt-6 text-sm font-semibold uppercase tracking-[0.22em] text-gold-light">{site.meta.title}</p>
            <h1 className="mt-3 text-5xl font-semibold leading-[1.02] tracking-tight sm:text-7xl">
              Dollars in.
              <span className="block text-gold-light">Pesos out.</span>
            </h1>
            <p className="mt-5 max-w-lg text-lg leading-snug text-on-night sm:text-xl">
              The month end close for Argentine companies that spend in dollars.
            </p>

            <ol className="mt-8 grid gap-4 sm:grid-cols-3">
              {DOES.map((d) => (
                <li key={d.title} className="flex gap-3 sm:flex-col sm:gap-2">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-night-2 text-gold ring-1 ring-night-line">
                    <svg viewBox="0 0 20 20" className="h-4.5 w-4.5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                      {d.icon}
                    </svg>
                  </span>
                  <span>
                    <span className="block text-sm font-semibold">{d.title}</span>
                    <span className="block text-sm leading-relaxed text-on-night-muted">{d.body}</span>
                  </span>
                </li>
              ))}
            </ol>

            <p className="mt-6 text-sm text-on-night-muted">
              A working demo on one synthetic month, {site.meta.period_label}, for a fictional company, {site.meta.company}.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <ButtonLink href="#results">
                See the close <Arrow />
              </ButtonLink>
              <ButtonLink href="#how" variant="light">
                How it works
              </ButtonLink>
            </div>
          </div>

          {/* The headline result: who closed the month */}
          <div className="rounded-3xl border border-night-line bg-night-2/80 p-5 backdrop-blur sm:p-8">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-on-night-muted">Who closed the month</p>
                <p className="num mt-2 text-4xl font-semibold sm:text-5xl">
                  {total} <span className="text-lg font-medium text-on-night-muted sm:text-xl">movements</span>
                </p>
              </div>
              <p className="text-sm text-on-night-muted">{s.receipts} receipts and invoices</p>
            </div>

            <div
              className="mt-6 flex h-14 w-full gap-[2px] overflow-hidden rounded-xl sm:h-16"
              role="img"
              aria-label={parts.map((p) => `${p.label}: ${p.n}`).join(', ')}
            >
              {parts.map((p, i) => (
                <div
                  key={p.who}
                  className={`grow-x ${WHO[p.who].barNight} ${i === 0 ? 'rounded-l-xl' : ''} ${i === parts.length - 1 ? 'rounded-r-xl' : ''}`}
                  style={{ width: `${(p.n / total) * 100}%`, animationDelay: `${i * 120}ms` }}
                />
              ))}
            </div>

            <div className="mt-5 grid grid-cols-3 gap-3 sm:gap-6">
              {parts.map((p) => (
                <div key={p.who}>
                  <p className="flex items-center gap-2 text-xs text-on-night-muted sm:text-sm">
                    <Dot who={p.who} night /> {p.label}
                  </p>
                  <p className="num mt-1 text-2xl font-semibold sm:text-4xl">{p.n}</p>
                  <p className="num text-xs text-on-night-muted">{pct(String(p.n / total), 0)} of movements</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* What we found */}
        <div className="mt-16">
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-gold-light">What we found</p>
          <dl className="mt-4 grid grid-cols-2 gap-px overflow-hidden rounded-3xl border border-night-line bg-night-line lg:grid-cols-3">
            {found.map((f) => (
              <div key={f.label} className="bg-night p-5 sm:p-6">
                <dt className="sr-only">{f.label}</dt>
                <dd className="num text-2xl font-semibold text-gold-light sm:text-3xl">{f.value}</dd>
                <dd className="mt-2 text-xs leading-relaxed text-on-night-muted sm:text-sm">{f.label}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </section>
  )
}

/** Thin decorative arcs, drawn once, behind the hero. */
function Curves() {
  return (
    <svg className="pointer-events-none absolute -right-40 -top-20 h-[760px] w-[760px] opacity-[0.22] sm:-right-24" viewBox="0 0 760 760" fill="none" aria-hidden>
      {[180, 260, 340, 420].map((r) => (
        <circle key={r} cx="560" cy="300" r={r} stroke="url(#arc)" strokeWidth="1" />
      ))}
      <defs>
        <linearGradient id="arc" x1="0" y1="0" x2="760" y2="760" gradientUnits="userSpaceOnUse">
          <stop stopColor="#dcc590" />
          <stop offset="1" stopColor="#dcc590" stopOpacity="0" />
        </linearGradient>
      </defs>
    </svg>
  )
}
