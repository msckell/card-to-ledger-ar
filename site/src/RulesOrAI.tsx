import { CartesianGrid, LabelList, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { pct, site } from './data'
import { Badge, Card, Check, Eyebrow, Section } from './ui'

// Chart colors mirror the tokens in index.css (Recharts needs literal values).
const INK = '#3b3b3f'
const GOLD = '#c29a45'
const GRID = '#e7e5e0'
const MUTED = '#7d7a74'

const ANOMALY_LABEL: Record<string, string> = {
  missing_receipt: 'Missing receipt',
  duplicate: 'Duplicate charge',
  amount_mismatch: 'Receipt differs from charge',
  refund_original_not_in_period: 'Refund of an earlier month',
}

function who(handledBy: string): 'rules' | 'ai' | 'review' {
  if (handledBy.startsWith('AI')) return 'ai'
  if (handledBy === 'Rules') return 'rules'
  return 'review'
}

export default function RulesOrAI() {
  const e = site.eval
  const thr = e.threshold
  const rec = thr.recommended_row
  const chart = thr.rows.map((r) => ({
    t: Number(r.threshold),
    share: Number(r.share_auto_accepted) * 100,
    accuracy: r.accuracy == null ? null : Number(r.accuracy) * 100,
  }))

  return (
    <Section
      id="rules-or-ai"
      tone="paper"
      eyebrow="Rules or AI?"
      title="When should AI decide on its own?"
      intro={
        <>
          The data generator wrote the correct answer for every movement, so every handoff is scored. The key product
          decision is how sure the AI must be before an account posts with no one looking.
        </>
      }
    >

      {thr.rows.length > 0 && (
        <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
          <Card className="p-5 sm:p-7">
            <Eyebrow>The confidence threshold</Eyebrow>
            <h3 className="mt-2 text-xl font-semibold tracking-tight">How sure must the AI be before an account posts on its own?</h3>
            <p className="mt-2 text-sm text-muted">
              For the {e.ai_accounts?.total} merchants no rule covers. A higher threshold accepts fewer suggestions, and the
              ones it accepts are more often right.
            </p>
            <div className="mt-6 h-72 w-full">
              <ResponsiveContainer>
                <LineChart data={chart} margin={{ top: 24, right: 92, bottom: 8, left: -16 }}>
                  <CartesianGrid stroke={GRID} vertical={false} />
                  <XAxis
                    dataKey="t"
                    type="number"
                    domain={['dataMin', 'dataMax']}
                    ticks={chart.map((c) => c.t)}
                    tick={{ fontSize: 11, fill: MUTED }}
                    tickFormatter={(v: number) => v.toFixed(2)}
                    stroke={GRID}
                  />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: MUTED }} tickFormatter={(v: number) => `${v}%`} stroke={GRID} />
                  <Tooltip
                    formatter={(v, name) => [`${Number(v).toFixed(1)}%`, name === 'share' ? 'Auto accepted' : 'Right, of those accepted']}
                    labelFormatter={(l) => `Threshold ${Number(l).toFixed(2)}`}
                    contentStyle={{ borderRadius: 12, border: `1px solid ${GRID}`, fontSize: 12 }}
                  />
                  {thr.recommended && (
                    <ReferenceLine
                      x={Number(thr.recommended)}
                      stroke="#141415"
                      strokeDasharray="3 3"
                      label={{ value: `Recommended ${thr.recommended}`, position: 'top', fontSize: 11, fill: '#141415', fontWeight: 600 }}
                    />
                  )}
                  <Line dataKey="share" stroke={INK} strokeWidth={2} dot={{ r: 4, strokeWidth: 0, fill: INK }} isAnimationActive={false}>
                    <LabelList dataKey="share" content={EndLabel('Auto accepted', INK)} />
                  </Line>
                  <Line dataKey="accuracy" stroke={GOLD} strokeWidth={2} dot={{ r: 4, strokeWidth: 0, fill: GOLD }} connectNulls isAnimationActive={false}>
                    <LabelList dataKey="accuracy" content={EndLabel('Right', '#8a6a2c')} />
                  </Line>
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted">
              <span className="inline-flex items-center gap-2"><span className="h-0.5 w-5 bg-rules" /> Share of suggestions auto accepted</span>
              <span className="inline-flex items-center gap-2"><span className="h-0.5 w-5 bg-ai" /> Share of the accepted ones that were right</span>
            </div>
          </Card>

          <div className="flex flex-col gap-5">
            <div className="rounded-3xl bg-night p-6 text-on-night sm:p-7">
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-gold-light">Recommended threshold</p>
              <p className="num mt-2 text-6xl font-semibold text-gold-light">{thr.recommended ?? 'None'}</p>
              {rec && (
                <div className="mt-5 grid grid-cols-3 gap-3 border-t border-night-line pt-5">
                  <Mini value={`${rec.accepted}/${e.ai_accounts?.total}`} label="auto accepted" />
                  <Mini value={pct(rec.accuracy)} label="of them right" />
                  <Mini value={String(rec.errors_accepted)} label="wrong, posted" />
                </div>
              )}
              <p className="mt-5 text-sm leading-relaxed text-on-night-muted">{thr.why}</p>
              {e.ai_accounts?.small_sample !== false && (
                <p className="mt-3 text-xs text-gold-light">Small sample. Read it as a direction, not a rate.</p>
              )}
            </div>
            <details className="group rounded-2xl border border-line bg-card p-5 text-sm">
              <summary className="cursor-pointer list-none font-semibold marker:hidden">
                <span className="inline-block transition-transform group-open:rotate-90">›</span> Every threshold, as a table
              </summary>
              <table className="mt-3 w-full text-xs">
                <thead>
                  <tr className="text-left text-faint">
                    <th className="py-1 font-medium">Threshold</th>
                    <th className="py-1 text-right font-medium">Accepted</th>
                    <th className="py-1 text-right font-medium">Right</th>
                    <th className="py-1 text-right font-medium">Wrong</th>
                  </tr>
                </thead>
                <tbody>
                  {thr.rows.map((r) => (
                    <tr key={r.threshold} className={r.threshold === thr.recommended ? 'font-semibold text-gold-text' : ''}>
                      <td className="num py-0.5">{r.threshold}</td>
                      <td className="num py-0.5 text-right">{r.accepted}</td>
                      <td className="num py-0.5 text-right">{pct(r.accuracy)}</td>
                      <td className="num py-0.5 text-right">{r.errors_accepted}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </details>
          </div>
        </div>
      )}

      <div className="mt-12">
        <Eyebrow>Every step, its owner and its score</Eyebrow>
        <div className="mt-4 divide-y divide-line overflow-hidden rounded-3xl border border-line bg-card">
          {e.decision_table.map((r) => (
            <details key={r.step} className="group">
              <summary className="grid cursor-pointer list-none grid-cols-[minmax(0,1fr)_auto] items-center gap-3 px-5 py-3.5 hover:bg-paper sm:grid-cols-[minmax(0,1fr)_auto_7rem] sm:gap-6 sm:px-7">
                <span className="flex items-center gap-2 text-sm font-semibold">
                  <span className="inline-block text-faint transition-transform group-open:rotate-90">›</span> {r.step}
                </span>
                <span className="hidden sm:block">
                  <Badge tone={who(r.handled_by)}>{r.handled_by}</Badge>
                </span>
                <span className="num text-right text-lg font-semibold">{r.headline}</span>
              </summary>
              <div className="px-5 pb-4 pl-10 text-sm leading-relaxed text-muted sm:px-7 sm:pl-12">
                <p className="sm:hidden">
                  <Badge tone={who(r.handled_by)}>{r.handled_by}</Badge>
                </p>
                <p className="mt-1">{r.why}</p>
                <p className="mt-1 text-xs text-faint">{/^\d/.test(r.headline) ? `${r.headline} ${r.note}` : `${r.headline}, ${r.note}`}</p>
              </div>
            </details>
          ))}
        </div>
      </div>

      <details className="group mt-6 rounded-3xl border border-line bg-card p-5 sm:p-7">
        <summary className="cursor-pointer list-none text-sm font-semibold">
          <span className="inline-block transition-transform group-open:rotate-90">›</span> See the detail: planted problems and
          receipt reading
        </summary>
        <div className="mt-2">
          <Eyebrow>Planted problems</Eyebrow>
          <h3 className="mt-2 text-xl font-semibold tracking-tight">The generator hid these on purpose. Did each one reach a person?</h3>
          <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
            {Object.entries(e.anomalies).map(([k, a]) => {
              const all = a.caught_in_review === a.planted
              return (
                <div key={k} className="rounded-2xl border border-line bg-card p-5">
                  <p className="flex items-center gap-2 text-sm font-semibold">
                    {all && <Check className="h-4 w-4 text-gold-text" />} {ANOMALY_LABEL[k] ?? k}
                  </p>
                  <p className="num mt-3 text-3xl font-semibold">
                    {a.caught_in_review}
                    <span className="text-lg text-faint">/{a.planted}</span>
                  </p>
                  <p className="text-xs text-faint">reached review · {a.true_positives} named exactly</p>
                </div>
              )
            })}
          </div>
          <p className="mt-3 max-w-3xl text-xs text-faint">
            “Named exactly” means the check that fired is the one the problem calls for. A problem can reach review under a
            different name, for example a refund of an earlier month linked tentatively by merchant.
          </p>
        </div>

        <div className="mt-12 grid gap-5 lg:grid-cols-[1fr_1.2fr] lg:items-center">
          <div>
            <Eyebrow>Reading {e.extraction.receipts} receipts</Eyebrow>
            <h3 className="mt-2 text-xl font-semibold tracking-tight">AI against a parser written for these exact layouts.</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              The template parser was written for the four synthetic layouts, so it is a ceiling, not a fair rival. Real
              receipts arrive in layouts nobody wrote a template for. That is where the AI reader earns its place, and why
              code still checks every amount it reads.
            </p>
          </div>
          <Card className="p-5">
            <div className="grid grid-cols-[1fr_auto_auto] gap-x-6 gap-y-2 text-sm">
              <span className="text-xs text-faint">Field</span>
              <span className="text-right text-xs text-faint">AI</span>
              <span className="text-right text-xs text-faint">Template parser</span>
              {['vendor', 'date', 'amount', 'currency', 'all_fields'].map((f) => (
                <Row key={f} label={f === 'all_fields' ? 'All four' : f[0].toUpperCase() + f.slice(1)} ai={e.extraction.ai?.[f]} tmpl={e.extraction.template[f]} strong={f === 'all_fields'} />
              ))}
            </div>
          </Card>
        </div>

      </details>

      {e.llm_usage && (
        <p className="mt-10 text-xs text-faint">
          Build time AI: {e.llm_usage.total_calls} calls, about USD {e.llm_usage.total_cost_usd.toFixed(2)} at API prices.
          Models: {Object.entries(e.llm_usage.models).map(([k, v]) => `${k} ${v}`).join(' · ')}. No AI runs when you open this page.
        </p>
      )}
    </Section>
  )
}

function Row({ label, ai, tmpl, strong }: { label: string; ai?: string; tmpl?: string; strong?: boolean }) {
  return (
    <>
      <span className={strong ? 'border-t border-line pt-2 font-semibold' : ''}>{label}</span>
      <span className={`num text-right ${strong ? 'border-t border-line pt-2 font-semibold text-gold-text' : ''}`}>{pct(ai)}</span>
      <span className={`num text-right text-muted ${strong ? 'border-t border-line pt-2' : ''}`}>{pct(tmpl)}</span>
    </>
  )
}

function Mini({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <p className="num text-xl font-semibold">{value}</p>
      <p className="text-[11px] leading-snug text-on-night-muted">{label}</p>
    </div>
  )
}

/** Direct label at the last point of a line, so the series never depends on color alone. */
function EndLabel(text: string, fill: string) {
  return function Label(props: { x?: number | string; y?: number | string; index?: number }) {
    if (props.index !== site.eval.threshold.rows.length - 1) return null
    return (
      <text x={Number(props.x) + 8} y={Number(props.y) + 4} fontSize={11} fontWeight={600} fill={fill}>
        {text}
      </text>
    )
  }
}
