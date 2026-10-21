import type { ReactNode } from 'react'
import { site, type Example } from './data'
import { Badge, Check, Cited, Mono, Section, WHO } from './ui'

const HEAD: Record<Example['path'], { title: string; line: string }> = {
  rules: { title: 'Rules handle it end to end', line: 'A known merchant with its receipt. No one needs to look.' },
  ai: { title: 'AI fills the gap', line: 'No rule knows this merchant. The AI suggests the account with high confidence.' },
  review: { title: 'A person decides', line: 'A rule knows the account, but the receipt is missing. It waits.' },
}

export default function Examples() {
  const threshold = site.eval.threshold.recommended
  return (
    <Section
      id="examples"
      tone="paper"
      eyebrow="Three real movements"
      title="Follow one charge down each path."
      intro="Taken from the September close as it is. Every figure on these cards is computed by code. Open the receipt PDFs to see what the AI read."
    >
      <div className="grid gap-5 lg:grid-cols-3">
        {site.examples.map((x) => (
          <article key={x.path} className="flex flex-col rounded-3xl border border-line bg-card p-5 sm:p-6">
            <div className="flex items-center gap-2">
              <span className={`h-2.5 w-2.5 rounded-full ${WHO[x.path].dot}`} aria-hidden />
              <span className="text-[11px] font-semibold uppercase tracking-[0.2em] text-faint">{WHO[x.path].label}</span>
            </div>
            <h3 className="mt-3 text-xl font-semibold tracking-tight">{HEAD[x.path].title}</h3>
            <p className="mt-1 text-sm text-muted">{HEAD[x.path].line}</p>

            <ol className="relative mt-6 space-y-5 border-l border-line pl-6">
              <Step n={1} title="In the export">
                <p className="font-semibold">{x.txn.descriptor}</p>
                <p className="num text-muted">
                  {x.txn.currency} {x.txn.amount} · {x.txn.date} · <Mono>{x.txn.id}</Mono>
                </p>
              </Step>

              <Step n={2} title="Converted to pesos">
                <p className="num">
                  {x.txn.currency} {x.txn.amount} × {x.txn.rate} = <span className="font-semibold">ARS {x.txn.ars}</span>
                </p>
                <p className="text-xs text-faint">Official seller rate of the posting day</p>
              </Step>

              <Step n={3} title="Receipt" warn={!x.receipt}>
                {x.receipt ? (
                  <>
                    <p>
                      {x.receipt.vendor} · <span className="num">{x.receipt.currency} {x.receipt.amount}</span>
                    </p>
                    <p className="text-xs text-muted">
                      <a href={x.receipt.file} target="_blank" rel="noreferrer" className="font-mono text-gold-text underline underline-offset-2">
                        {x.receipt.id}.pdf
                      </a>{' '}
                      · read by {x.receipt.read_by}, amount checked by code
                    </p>
                  </>
                ) : (
                  <p className="text-review">No receipt found in the matching window</p>
                )}
              </Step>

              <Step n={4} title="Account" ai={x.coding?.by === 'ai'}>
                {x.coding?.by === 'rule' && (
                  <>
                    <p className="font-semibold">{x.coding.account}</p>
                    <p className="text-xs text-muted">
                      Rule <Mono>{x.coding.id}</Mono> matches <Mono className="rounded bg-paper px-1 ring-1 ring-line">{x.coding.pattern}</Mono>
                    </p>
                  </>
                )}
                {x.coding?.by === 'ai' && (
                  <>
                    <p className="font-semibold">{x.coding.account}</p>
                    <Confidence value={Number(x.coding.confidence)} threshold={threshold ? Number(threshold) : null} label={x.coding.confidence} />
                    <p className="mt-2 text-xs leading-relaxed text-muted">“{x.coding.reason}”</p>
                  </>
                )}
              </Step>

              {x.exception && (
                <Step n={5} title="Exception" warn>
                  <p className="font-semibold">{x.exception.title}</p>
                  <p className="mt-1 text-xs leading-relaxed text-muted">
                    <Cited text={x.exception.explanation} />
                  </p>
                  <p className="mt-2">
                    <Badge tone={x.exception.source === 'ai_verified' ? 'ai' : 'neutral'}>
                      {x.exception.source === 'ai_verified' ? 'Written by AI, verified' : 'Template'}
                    </Badge>
                  </p>
                </Step>
              )}

              <Step n={x.exception ? 6 : 5} title={x.posting.status === 'posted' ? 'Posted' : 'Held for review'} done={x.posting.status === 'posted'}>
                <p className="font-semibold">{x.posting.account}</p>
                <p className="text-xs text-muted">
                  <Mono>{x.posting.line}</Mono> · {x.posting.approved_by}
                </p>
              </Step>
            </ol>
          </article>
        ))}
      </div>
    </Section>
  )
}

function Step({ n, title, children, warn, ai, done }: { n: number; title: string; children: ReactNode; warn?: boolean; ai?: boolean; done?: boolean }) {
  const dot = done ? 'bg-night text-gold' : warn ? 'bg-review text-white' : ai ? 'bg-ai text-night' : 'bg-card text-faint ring-1 ring-line'
  return (
    <li className="relative text-sm">
      <span className={`num absolute -left-[37px] top-0 flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-semibold ${dot}`}>
        {done ? <Check className="h-3.5 w-3.5" /> : n}
      </span>
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">{title}</p>
      <div className="mt-1 leading-relaxed [overflow-wrap:anywhere]">{children}</div>
    </li>
  )
}

function Confidence({ value, threshold, label }: { value: number; threshold: number | null; label: string }) {
  return (
    <div className="mt-2">
      <div className="relative h-2 rounded-full bg-paper ring-1 ring-line">
        <div className="grow-x h-2 rounded-full bg-ai" style={{ width: `${value * 100}%` }} />
        {threshold != null && (
          <div className="absolute -top-1 h-4 w-px bg-ink" style={{ left: `${threshold * 100}%` }} title={`Threshold ${threshold}`} />
        )}
      </div>
      <p className="num mt-1 text-xs text-muted">
        Confidence {label}
        {threshold != null && <> · auto accepted at {threshold.toFixed(2)} or more</>}
      </p>
    </div>
  )
}
