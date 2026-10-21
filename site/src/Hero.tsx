import type { ReactNode } from 'react'
import { pct, site } from './data'
import { Arrow, Badge, ButtonLink, Check, Dot, GoldRule, WHO, type Who } from './ui'

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

  return (
    <section id="top" className="relative overflow-hidden bg-night text-on-night">
      <Curves />
      <div className="relative mx-auto max-w-6xl px-4 pb-16 pt-14 sm:px-6 sm:pb-24 sm:pt-20">
        <div className="grid items-center gap-14 lg:grid-cols-[1.05fr_1fr] lg:gap-12">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="gold">Close of {site.meta.period_label}</Badge>
              <Badge tone="night">Fictional company · synthetic data</Badge>
            </div>

            <GoldRule className="mt-10" />
            <h1 className="mt-6 max-w-4xl text-[2.4rem] font-semibold leading-[1.08] tracking-tight sm:text-6xl lg:text-[3.6rem]">
              A month of dollar spending, <span className="text-gold-light">closed in pesos</span> and ready to review.
            </h1>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-on-night-muted sm:text-lg">
              {site.meta.company} spends in dollars and keeps its books in pesos. Rules do everything they can, AI handles only
              what rules cannot, and a person reviews the rest. Every split is measured against known correct answers.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <ButtonLink href="#results">
                See the close <Arrow />
              </ButtonLink>
              <ButtonLink href="#how" variant="light">
                How it works
              </ButtonLink>
            </div>
            <p className="mt-5 text-xs text-on-night-muted">{site.meta.subtitle}</p>
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
              <p className="text-sm text-on-night-muted">{s.receipts} receipts and invoices, matched by code</p>
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

        {/* Four proof points */}
        <dl className="mt-10 grid grid-cols-2 gap-px overflow-hidden rounded-3xl border border-night-line bg-night-line lg:grid-cols-4">
          <Kpi
            value={
              <>
                USD {s.spend_usd_compact} <Arrow className="mx-0.5 inline text-gold" /> ARS {s.spend_ars_compact}
              </>
            }
            label="Spend converted at the official rate of each day"
          />
          <Kpi value={`${caught}/${planted}`} label="Planted problems that reached a person" />
          <Kpi
            value={rec ? pct(rec.accuracy) : 'n/a'}
            label={rec ? `Of AI account suggestions accepted at ${e.threshold.recommended} were right` : 'AI not run'}
          />
          <Kpi
            value={
              <span className="inline-flex items-center gap-2">
                <Check className="h-6 w-6 text-gold" /> Debe = Haber
              </span>
            }
            label={`Journal entry balanced to the cent, ARS ${site.journal.totals.debe}`}
          />
        </dl>
      </div>
    </section>
  )
}

function Kpi({ value, label }: { value: ReactNode; label: string }) {
  return (
    <div className="bg-night p-5 sm:p-6">
      <dt className="sr-only">{label}</dt>
      <dd className="num text-xl font-semibold text-gold-light sm:text-2xl lg:text-xl xl:text-2xl">{value}</dd>
      <dd className="mt-2 text-xs leading-relaxed text-on-night-muted sm:text-sm">{label}</dd>
    </div>
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
