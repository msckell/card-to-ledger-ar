import { site } from './data'
import { Dot, Eyebrow, Section } from './ui'

// Diagram geometry, in viewBox units. Every width is proportional to a count from site.flow.
const W = 360
const PAD = 8
const GAP = 12
const NODE_H = 28
const Y = { top: 44, mid: 196, bottom: 348 }

const FILL = {
  all: '#f4f2ee',
  rules: '#d9d6cf',
  ai: '#c29a45',
  review: '#7f93ad',
}

type Span = [number, number]

function band(a: Span, ya: number, b: Span, yb: number) {
  const ym = (ya + yb) / 2
  return `M${a[0]},${ya} C${a[0]},${ym} ${b[0]},${ym} ${b[0]},${yb} L${b[1]},${yb} C${b[1]},${ym} ${a[1]},${ym} ${a[1]},${ya} Z`
}

export default function Flow() {
  const f = site.flow
  const review = f.rules_to_review + f.ai_to_review
  const k = (W - 2 * PAD - 2 * GAP) / f.total

  const topX = PAD + (W - 2 * PAD - f.total * k) / 2
  const midX = PAD + (W - 2 * PAD - f.total * k - GAP) / 2
  const rule: Span = [midX, midX + f.by_rule * k]
  const noRule: Span = [rule[1] + GAP, rule[1] + GAP + f.no_rule * k]
  const outRules: Span = [PAD, PAD + f.rules_resolved * k]
  const outReview: Span = [outRules[1] + GAP, outRules[1] + GAP + review * k]
  const outAi: Span = [outReview[1] + GAP, outReview[1] + GAP + f.ai_resolved * k]

  const topBot = Y.top + NODE_H
  const midBot = Y.mid + NODE_H
  const bands = [
    { d: band([topX, topX + f.by_rule * k], topBot, rule, Y.mid), fill: FILL.rules, t: `${f.by_rule} movements matched a rule` },
    { d: band([topX + f.by_rule * k, topX + f.total * k], topBot, noRule, Y.mid), fill: FILL.ai, t: `${f.no_rule} movements had no rule` },
    { d: band([rule[0], rule[0] + f.rules_resolved * k], midBot, outRules, Y.bottom), fill: FILL.rules, t: `${f.rules_resolved} posted by rules` },
    {
      d: band([rule[0] + f.rules_resolved * k, rule[1]], midBot, [outReview[0], outReview[0] + f.rules_to_review * k], Y.bottom),
      fill: FILL.review,
      t: `${f.rules_to_review} had a rule but an open problem`,
    },
    {
      d: band([noRule[0], noRule[0] + f.ai_to_review * k], midBot, [outReview[0] + f.rules_to_review * k, outReview[1]], Y.bottom),
      fill: FILL.review,
      t: `${f.ai_to_review} AI coded movements still went to a person`,
    },
    { d: band([noRule[0] + f.ai_to_review * k, noRule[1]], midBot, outAi, Y.bottom), fill: FILL.ai, t: `${f.ai_resolved} posted from AI` },
  ]
  const maxReason = Math.max(...f.review_reasons.map((r) => r.n))
  const spend = site.spend_by_account
  const maxSpend = Math.max(...spend.map((r) => r.cents))

  return (
    <Section
      id="results"
      tone="night"
      eyebrow="The result"
      title={
        <>
          {f.total} movements in. <span className="text-gold-light">{f.rules_resolved + f.ai_resolved} posted</span>{' '}
          without anyone touching them.
        </>
      }
      intro={
        <>
          Follow the month from top to bottom. Each band is as wide as the number of movements in it. Anything with an open
          question, even if a rule knew the account, stops and waits for a person.
        </>
      }
    >
      <div className="grid gap-10 lg:grid-cols-[1.15fr_1fr] lg:gap-16">
        <figure>
          <svg viewBox={`0 0 ${W} 420`} className="w-full" role="img" aria-labelledby="flow-title">
            <title id="flow-title">
              {`${f.total} movements: ${f.by_rule} matched a rule, ${f.no_rule} had none. ${f.rules_resolved} posted by rules, ${f.ai_resolved} posted from AI, ${review} sent to a person.`}
            </title>
            {bands.map((b, i) => (
              <path key={i} d={b.d} fill={b.fill} fillOpacity={0.28} className="transition-[fill-opacity] hover:[fill-opacity:0.6]">
                <title>{b.t}</title>
              </path>
            ))}

            {/* Top */}
            <rect x={topX} y={Y.top} width={f.total * k} height={NODE_H} rx={6} fill={FILL.all} />
            <text x={W / 2} y={Y.top + 19} textAnchor="middle" className="num fill-night text-[14px] font-semibold">
              {f.total} movements in the export
            </text>

            {/* Middle */}
            <rect x={rule[0]} y={Y.mid} width={rule[1] - rule[0]} height={NODE_H} rx={6} fill={FILL.rules} />
            <text x={rule[0] + 10} y={Y.mid + 19} className="num fill-night text-[13.5px] font-semibold">
              {f.by_rule} · a rule knows the merchant
            </text>
            <rect x={noRule[0]} y={Y.mid} width={noRule[1] - noRule[0]} height={NODE_H} rx={6} fill={FILL.ai} />
            <text x={(noRule[0] + noRule[1]) / 2} y={Y.mid + 19} textAnchor="middle" className="num fill-night text-[13.5px] font-semibold">
              {f.no_rule}
            </text>
            <text
              x={noRule[1]}
              y={Y.mid - 10}
              textAnchor="end"
              className="fill-gold-light text-[12.5px] font-semibold"
              stroke="#0b0b0c"
              strokeWidth={4}
              paintOrder="stroke"
            >
              No rule · AI suggests an account
            </text>

            {/* Bottom */}
            {[
              { s: outRules, n: f.rules_resolved, fill: FILL.rules, label: 'Posted by rules', anchor: 'start' as const, x: outRules[0] },
              { s: outReview, n: review, fill: FILL.review, label: 'A person', anchor: 'middle' as const, x: (outReview[0] + outReview[1]) / 2 },
              { s: outAi, n: f.ai_resolved, fill: FILL.ai, label: 'AI', anchor: 'end' as const, x: outAi[1] },
            ].map((o) => (
              <g key={o.label}>
                <rect x={o.s[0]} y={Y.bottom} width={o.s[1] - o.s[0]} height={NODE_H} rx={6} fill={o.fill} />
                <text x={(o.s[0] + o.s[1]) / 2} y={Y.bottom + 19} textAnchor="middle" className="num fill-night text-[13.5px] font-bold">
                  {o.n}
                </text>
                <text x={o.x} y={Y.bottom + NODE_H + 22} textAnchor={o.anchor} className="fill-on-night text-[13px] font-semibold">
                  {o.label}
                </text>
              </g>
            ))}
          </svg>
          <figcaption className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-xs text-on-night-muted">
            <span className="inline-flex items-center gap-2"><Dot who="rules" night /> Rules</span>
            <span className="inline-flex items-center gap-2"><Dot who="ai" night /> AI</span>
            <span className="inline-flex items-center gap-2"><Dot who="review" night /> A person</span>
            <span className="hidden sm:inline">Hover a band for its count.</span>
          </figcaption>
        </figure>

        <div className="space-y-10">
          <div>
            <Eyebrow night>Why {review} went to a person</Eyebrow>
            <ul className="mt-4 space-y-3">
              {f.review_reasons.map((r) => (
                <li key={r.type}>
                  <div className="flex items-baseline justify-between gap-3 text-sm">
                    <span>{r.title}</span>
                    <span className="num font-semibold">{r.n}</span>
                  </div>
                  <div className="mt-1.5 h-2 rounded-full bg-night-2">
                    <div className="grow-x stripes h-2 rounded-full bg-review-night" style={{ width: `${(r.n / maxReason) * 100}%` }} />
                  </div>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-on-night-muted">Main reason per movement. A movement can carry more than one.</p>
          </div>

          <div>
            <Eyebrow night>Where the pesos went</Eyebrow>
            <ul className="mt-4 space-y-2.5">
              {spend.map((r) => (
                <li key={r.account} title={`${r.account} ${r.name}: ARS ${r.ars}`}>
                  <div className="flex items-baseline justify-between gap-3 text-[13px]">
                    <span className={`truncate ${r.pending ? 'text-review-night' : ''}`}>
                      {r.name}
                      {r.pending && ' (in review)'}
                    </span>
                    <span className="num shrink-0 text-on-night-muted">ARS {r.ars_compact}</span>
                  </div>
                  <div className="mt-1 h-1.5 rounded-full bg-night-2">
                    <div
                      className={`grow-x h-1.5 rounded-full ${r.pending ? 'stripes bg-review-night' : 'bg-gold'}`}
                      style={{ width: `${Math.max((r.cents / maxSpend) * 100, 1)}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-on-night-muted">
              Net debit per expense account in the September entry. Items in review sit in a suspense account until a
              person decides.
            </p>
          </div>
        </div>
      </div>
    </Section>
  )
}
