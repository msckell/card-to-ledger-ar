import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { pct, site } from './data'
import { Badge, Card, Section } from './ui'

const ANOMALY_LABEL: Record<string, string> = {
  missing_receipt: 'Missing receipt',
  duplicate: 'Duplicate charge',
  amount_mismatch: 'Receipt differs from charge',
  refund_original_not_in_period: 'Refund of an earlier month',
}

export default function RulesOrAI() {
  const e = site.eval
  const s = site.summary
  const thr = e.threshold
  const chart = thr.rows.map((r) => ({
    t: Number(r.threshold),
    share: Number(r.share_auto_accepted) * 100,
    accuracy: r.accuracy == null ? null : Number(r.accuracy) * 100,
    accepted: r.accepted,
  }))
  const rec = thr.recommended_row
  return (
    <Section
      id="rules-or-ai"
      eyebrow="4 · Rules or AI?"
      title="Every split, measured"
      intro={
        <>
          Of {s.transactions} movements, rules resolved {s.split.rules}, the AI resolved {s.split.ai}
          {e.ai_accounts && <> with {pct(rec?.accuracy ?? null)} accuracy on what it accepted</>}, and {s.split.review} went to a
          person. The generator wrote the correct answer for every movement, so each step below is scored against it.
        </>
      }
    >
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-line bg-paper text-left text-xs uppercase tracking-wide text-muted">
                <th className="px-4 py-2.5 font-medium">Step</th>
                <th className="px-4 py-2.5 font-medium">Handled by</th>
                <th className="px-4 py-2.5 font-medium">Why</th>
                <th className="px-4 py-2.5 font-medium">Measured</th>
              </tr>
            </thead>
            <tbody>
              {e.decision_table.map((r) => (
                <tr key={r.step} className="border-b border-line align-top last:border-0">
                  <td className="px-4 py-3 font-medium">{r.step}</td>
                  <td className="px-4 py-3">
                    <Badge tone={r.handled_by.startsWith('AI') ? 'ai' : r.handled_by === 'Rules' ? 'rules' : 'review'}>
                      {r.handled_by}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-muted">{r.why}</td>
                  <td className="num px-4 py-3">{r.accuracy}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {thr.rows.length > 0 && (
        <div className="mt-10 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <Card className="p-4 sm:p-5">
            <h3 className="font-serif text-lg font-semibold">The confidence threshold</h3>
            <p className="mt-1 text-sm text-muted">
              For the {e.ai_accounts?.total} merchants no rule covers: raising the threshold accepts fewer AI suggestions,
              and the ones it accepts are more often right.
            </p>
            <div className="mt-4 h-64 w-full">
              <ResponsiveContainer>
                <LineChart data={chart} margin={{ top: 8, right: 12, bottom: 4, left: -12 }}>
                  <CartesianGrid stroke="#e2e0d8" vertical={false} />
                  <XAxis dataKey="t" type="number" domain={[0.5, 0.95]} ticks={chart.map((c) => c.t)} tick={{ fontSize: 11 }} tickFormatter={(v: number) => v.toFixed(2)} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} tickFormatter={(v: number) => `${v}%`} />
                  <Tooltip
                    formatter={(v, name) => [`${Number(v).toFixed(1)}%`, name === 'share' ? 'Auto accepted' : 'Accuracy of accepted']}
                    labelFormatter={(l) => `Threshold ${Number(l).toFixed(2)}`}
                  />
                  <Legend formatter={(v) => (v === 'share' ? 'Share auto accepted' : 'Accuracy of accepted')} wrapperStyle={{ fontSize: 12 }} />
                  {thr.target && <ReferenceLine y={Number(thr.target) * 100} stroke="#a3621a" strokeDasharray="4 4" />}
                  {thr.recommended && <ReferenceLine x={Number(thr.recommended)} stroke="#1b1d1c" strokeDasharray="2 3" />}
                  <Line dataKey="share" stroke="#3d5a99" strokeWidth={2} dot={{ r: 3 }} isAnimationActive={false} />
                  <Line dataKey="accuracy" stroke="#1d3b2f" strokeWidth={2} dot={{ r: 3 }} connectNulls isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-2 text-xs text-faint">
              Dashed horizontal line: target accuracy {pct(thr.target, 0)}. Dotted vertical line: recommended threshold.
            </p>
          </Card>
          <Card className="p-4 sm:p-5">
            <p className="text-xs font-medium uppercase tracking-wide text-faint">Recommended threshold</p>
            <p className="num mt-1 font-serif text-4xl font-semibold text-ai">{thr.recommended ?? 'None'}</p>
            {rec && (
              <p className="mt-2 text-sm">
                Auto accepts {rec.accepted} of {e.ai_accounts?.total} suggestions ({pct(rec.share_auto_accepted, 0)}), with{' '}
                {pct(rec.accuracy)} of them right and {rec.errors_accepted} wrong.
                {s.ai_confident_but_in_review > 0 && (
                  <>
                    {' '}
                    {s.ai_confident_but_in_review} of those still went to a person because of another open exception, such as a
                    missing receipt, which leaves {s.split.ai} resolved by AI.
                  </>
                )}
              </p>
            )}
            <p className="mt-3 text-sm text-muted">{thr.why}</p>
            {e.ai_accounts?.small_sample !== false && (
              <p className="mt-3 text-xs text-review">Small sample. Read it as a direction, not a rate.</p>
            )}
            <table className="mt-4 w-full text-xs">
              <thead>
                <tr className="text-left text-faint">
                  <th className="py-1 font-medium">Threshold</th>
                  <th className="py-1 text-right font-medium">Accepted</th>
                  <th className="py-1 text-right font-medium">Accuracy</th>
                </tr>
              </thead>
              <tbody>
                {thr.rows.map((r) => (
                  <tr key={r.threshold} className={r.threshold === thr.recommended ? 'font-semibold text-ai' : ''}>
                    <td className="num py-0.5">{r.threshold}</td>
                    <td className="num py-0.5 text-right">{r.accepted}</td>
                    <td className="num py-0.5 text-right">{pct(r.accuracy)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      )}

      <div className="mt-10 grid gap-6 lg:grid-cols-2">
        <Card className="p-4 sm:p-5">
          <h3 className="font-serif text-lg font-semibold">Planted problems</h3>
          <p className="mt-1 text-sm text-muted">The generator hid these on purpose. Did they reach a person?</p>
          <table className="mt-3 w-full text-sm">
            <thead>
              <tr className="border-b border-line text-left text-xs text-faint">
                <th className="py-1.5 font-medium">Problem</th>
                <th className="py-1.5 text-right font-medium">Planted</th>
                <th className="py-1.5 text-right font-medium">Sent to review</th>
                <th className="py-1.5 text-right font-medium">Named exactly</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(e.anomalies).map(([k, a]) => (
                <tr key={k} className="border-b border-line last:border-0">
                  <td className="py-1.5">{ANOMALY_LABEL[k] ?? k}</td>
                  <td className="num py-1.5 text-right">{a.planted}</td>
                  <td className="num py-1.5 text-right">{a.caught_in_review}</td>
                  <td className="num py-1.5 text-right">{a.true_positives}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-xs text-faint">
            “Named exactly” means the check that fired is the one the problem calls for. A problem can reach review under
            a different name, for example a refund of an earlier month linked tentatively by merchant.
          </p>
        </Card>
        <Card className="p-4 sm:p-5">
          <h3 className="font-serif text-lg font-semibold">Reading {e.extraction.receipts} receipts</h3>
          <p className="mt-1 text-sm text-muted">Share of receipts read right, field by field.</p>
          <table className="mt-3 w-full text-sm">
            <thead>
              <tr className="border-b border-line text-left text-xs text-faint">
                <th className="py-1.5 font-medium">Field</th>
                <th className="py-1.5 text-right font-medium">AI</th>
                <th className="py-1.5 text-right font-medium">Template parser</th>
              </tr>
            </thead>
            <tbody>
              {['vendor', 'date', 'amount', 'currency', 'all_fields'].map((f) => (
                <tr key={f} className="border-b border-line last:border-0">
                  <td className="py-1.5">{f === 'all_fields' ? 'All four' : f[0].toUpperCase() + f.slice(1)}</td>
                  <td className="num py-1.5 text-right">{pct(e.extraction.ai?.[f])}</td>
                  <td className="num py-1.5 text-right">{pct(e.extraction.template[f])}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-xs text-faint">
            The template parser was written for these four synthetic layouts, so it is a ceiling, not a fair rival. Real
            receipts arrive in layouts nobody wrote a template for. That is where the AI reader earns its place, and why
            code still checks every amount it reads.
          </p>
        </Card>
      </div>
      {e.llm_usage && (
        <p className="mt-6 text-xs text-faint">
          Build time AI: {e.llm_usage.total_calls} calls, about USD {e.llm_usage.total_cost_usd.toFixed(2)} at API prices.
          Models: {Object.entries(e.llm_usage.models).map(([k, v]) => `${k} ${v}`).join(' · ')}. No AI runs when you open this page.
        </p>
      )}
    </Section>
  )
}
