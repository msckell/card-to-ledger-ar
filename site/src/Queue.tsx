import { useMemo, useState } from 'react'
import { site, type QueueItem } from './data'
import { Badge, Card, Cited, Section } from './ui'

const ORDER = [
  'duplicate_suspected',
  'amount_mismatch',
  'missing_receipt',
  'ai_below_threshold',
  'refund_partial_link',
  'refund_original_not_found',
  'receipt_unmatched',
  'receipt_unreadable',
  'no_rule',
]

export default function Queue() {
  const items = site.queue
  const types = useMemo(() => {
    const count = new Map<string, { title: string; n: number }>()
    for (const q of items) {
      const c = count.get(q.type) ?? { title: q.title, n: 0 }
      c.n += 1
      count.set(q.type, c)
    }
    return [...count.entries()].sort((a, b) => ORDER.indexOf(a[0]) - ORDER.indexOf(b[0]))
  }, [items])
  const [filter, setFilter] = useState<string>(types[0]?.[0] ?? '')
  const [showAll, setShowAll] = useState(false)
  const shown = items.filter((q) => q.type === filter)
  const visible = showAll ? shown : shown.slice(0, 6)

  return (
    <Section
      id="queue"
      eyebrow="2 · Review queue"
      title="What a controller works through"
      intro={
        <>
          {items.length} exceptions, each with the movement, the receipt evidence, the AI suggestion when there is one,
          and a plain explanation. The numbers in the grey line come from code. The sentence under it is written by
          AI and checked by a verifier, or by a template when the AI text failed the check. Everything here sits in a
          suspense account until a person decides.
        </>
      }
    >
      <div className="-mx-4 overflow-x-auto px-4 pb-1">
        <div className="flex gap-2">
          {types.map(([t, c]) => (
            <button
              key={t}
              onClick={() => {
                setFilter(t)
                setShowAll(false)
              }}
              className={`shrink-0 rounded-full border px-3 py-1.5 text-sm transition ${
                filter === t ? 'border-ink bg-ink text-white' : 'border-line bg-card text-ink hover:border-faint'
              }`}
            >
              {c.title} <span className="num opacity-70">{c.n}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="mt-5 grid gap-3">
        {visible.map((q) => (
          <Item key={q.id} q={q} />
        ))}
      </div>
      {shown.length > visible.length && (
        <button onClick={() => setShowAll(true)} className="mt-4 text-sm font-medium text-accent underline underline-offset-4">
          Show all {shown.length}
        </button>
      )}
    </Section>
  )
}

function Item({ q }: { q: QueueItem }) {
  const t = q.txn
  return (
    <Card className="p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-faint">{q.id}</span>
          <span className="text-sm font-semibold">{q.title}</span>
        </div>
        <Badge tone="review">{q.status}</Badge>
      </div>

      {t && (
        <div className="mt-3 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
          <p>
            <span className="font-mono text-xs text-faint">{t.id}</span> <span className="font-medium">{t.descriptor}</span>
          </p>
          <p className="num sm:text-right">
            {t.currency} {t.amount} <span className="text-faint">· ARS {t.ars} at {t.rate}</span>
          </p>
          <p className="text-muted">
            {t.date}
            {t.cardholder && ` · ${t.cardholder}`}
            {t.memo && <span className="italic"> · “{t.memo}”</span>}
          </p>
          {t.proposed_account && <p className="text-muted sm:text-right">Proposed: {t.proposed_account}</p>}
        </div>
      )}

      {(q.receipt || q.ai) && (
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          {q.receipt && (
            <div className="rounded-md bg-paper p-3 text-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-faint">Receipt evidence</p>
              <p className="mt-1">
                <a href={q.receipt.file} target="_blank" rel="noreferrer" className="font-mono text-xs text-accent underline underline-offset-2">
                  {q.receipt.id}.pdf
                </a>{' '}
                {q.receipt.vendor}
              </p>
              <p className="num text-muted">
                {q.receipt.date} · {q.receipt.currency ?? 'no currency'} {q.receipt.amount ?? 'no amount'}
              </p>
            </div>
          )}
          {q.ai && (
            <div className="rounded-md bg-ai-soft p-3 text-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-ai">
                AI suggestion {q.ai.id} · confidence {q.ai.confidence}
              </p>
              <p className="mt-1 font-medium">{q.ai.account}</p>
              <p className="text-muted">{q.ai.reason}</p>
            </div>
          )}
        </div>
      )}

      <p className="mt-3 rounded-md border border-line bg-paper px-3 py-2 font-mono text-[12px] leading-relaxed text-muted">{q.facts}</p>
      <p className="mt-3 text-[15px] leading-relaxed">
        <Cited text={q.explanation} />{' '}
        <Badge tone={q.explanation_source === 'ai_verified' ? 'ai' : 'neutral'}>
          {q.explanation_source === 'ai_verified' ? 'AI, verified' : 'Template'}
        </Badge>
      </p>
      <p className="mt-2 text-sm text-muted">
        Next step: <span className="text-ink">{q.next_step}</span>
      </p>
    </Card>
  )
}
