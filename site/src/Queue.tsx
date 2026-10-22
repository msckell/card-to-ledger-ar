import { useMemo, useState } from 'react'
import { site, type QueueItem } from './data'
import { Badge, Cited, Mono, Section } from './ui'

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

const PAGE = 8
const ALL = 'all'

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
  const tabs: [string, { title: string; n: number }][] = [[ALL, { title: 'All', n: items.length }], ...types]
  const [filter, setFilter] = useState<string>(ALL)
  const [showAll, setShowAll] = useState(false)
  const shown = filter === ALL ? items : items.filter((q) => q.type === filter)
  const pending = site.spend_by_account.find((a) => a.pending)
  const visible = showAll ? shown : shown.slice(0, PAGE)

  return (
    <Section
      id="queue"
      eyebrow="The controller's view"
      title={
        <>
          {items.length} open questions, each with its evidence and a next step.
        </>
      }
      intro="This is the review queue a controller works through. Facts and figures come from code. The plain sentence is written by AI and checked by the verifier. Nothing here posts until a person decides, so these items wait in a suspense account."
    >
      {pending && (
        <div className="mb-8 flex flex-wrap items-end gap-x-6 gap-y-2">
          <p className="num text-4xl font-semibold sm:text-5xl">
            ARS {pending.ars_compact}
          </p>
          <p className="pb-1 text-sm text-muted">
            waiting for a decision, across {site.summary.split.review} movements held in a suspense account
          </p>
        </div>
      )}

      <div className="-mx-4 overflow-x-auto px-4 pb-1 sm:mx-0 sm:px-0">
        <div className="flex gap-2 sm:flex-wrap" role="tablist" aria-label="Exception type">
          {tabs.map(([t, c]) => (
            <button
              key={t}
              role="tab"
              aria-selected={filter === t}
              onClick={() => {
                setFilter(t)
                setShowAll(false)
              }}
              className={`shrink-0 rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                filter === t ? 'bg-night text-on-night' : 'bg-card text-ink ring-1 ring-line hover:ring-faint'
              }`}
            >
              {c.title} <span className={`num ml-1 ${filter === t ? 'text-gold-light' : 'text-faint'}`}>{c.n}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6 divide-y divide-line overflow-hidden rounded-3xl border border-line bg-card">
        {visible.map((q) => (
          <Row key={q.id} q={q} />
        ))}
      </div>
      {shown.length > visible.length && (
        <button
          onClick={() => setShowAll(true)}
          className="mt-5 rounded-full bg-card px-5 py-2.5 text-sm font-semibold ring-1 ring-line hover:ring-faint"
        >
          Show all {shown.length}
        </button>
      )}
    </Section>
  )
}

function Row({ q }: { q: QueueItem }) {
  const t = q.txn
  return (
    <details className="group">
      <summary className="grid cursor-pointer list-none grid-cols-[minmax(0,1fr)_auto] items-center gap-3 px-4 py-3.5 hover:bg-paper sm:grid-cols-[11rem_minmax(0,1fr)_minmax(0,1fr)_7rem] sm:gap-5 sm:px-6">
        <span className="hidden text-xs font-semibold text-review sm:block">{q.title}</span>
        <span className="min-w-0">
          <span className="flex items-center gap-2">
            <span className="inline-block text-faint transition-transform group-open:rotate-90">›</span>
            <span className="truncate text-sm font-semibold">{t ? t.descriptor : q.title}</span>
          </span>
          <span className="block pl-4 text-xs text-faint sm:hidden">{q.title}</span>
        </span>
        <span className="hidden truncate text-sm text-muted sm:block">{q.next_step}</span>
        <span className="num text-right text-sm font-semibold">{t ? `${t.currency} ${t.amount}` : ''}</span>
      </summary>
      <div className="px-4 pb-5 sm:px-6">
        <Item q={q} />
      </div>
    </details>
  )
}

function Item({ q }: { q: QueueItem }) {
  const t = q.txn
  return (
    <article className="rounded-2xl bg-paper p-5 ring-1 ring-line sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-faint">
            {q.title} · <Mono>{q.id}</Mono>
          </p>
          {t && <p className="mt-1.5 text-lg font-semibold [overflow-wrap:anywhere]">{t.descriptor}</p>}
          {t && (
            <p className="text-sm text-muted">
              {t.date}
              {t.cardholder && ` · ${t.cardholder}`}
              {t.memo && <span className="italic"> · “{t.memo}”</span>}
            </p>
          )}
        </div>
        {t && (
          <div className="text-right">
            <p className="num text-lg font-semibold">
              {t.currency} {t.amount}
            </p>
            <p className="num text-xs text-faint">
              ARS {t.ars} at {t.rate}
            </p>
          </div>
        )}
      </div>

      <p className="mt-4 text-[15px] leading-relaxed">
        <Cited text={q.explanation} />
      </p>

      {(q.receipt || q.ai) && (
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {q.receipt && (
            <div className="rounded-2xl bg-card p-4 text-sm ring-1 ring-line">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">Receipt evidence</p>
              <p className="mt-1.5">
                {q.receipt.vendor}{' '}
                <a href={q.receipt.file} target="_blank" rel="noreferrer" className="font-mono text-xs text-gold-text underline underline-offset-2">
                  {q.receipt.id}.pdf
                </a>
              </p>
              <p className="num text-muted">
                {q.receipt.date} · {q.receipt.currency ?? 'no currency'} {q.receipt.amount ?? 'no amount'}
              </p>
            </div>
          )}
          {q.ai && (
            <div className="rounded-2xl bg-gold-soft p-4 text-sm">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-gold-text">
                AI suggestion · confidence {q.ai.confidence}
              </p>
              <p className="mt-1.5 font-semibold">{q.ai.account}</p>
              <p className="text-muted">{q.ai.reason}</p>
            </div>
          )}
        </div>
      )}

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-4">
        <p className="text-sm">
          <span className="text-faint">Next step </span>
          <span className="font-semibold">{q.next_step}</span>
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={q.explanation_source === 'ai_verified' ? 'ai' : 'neutral'}>
            {q.explanation_source === 'ai_verified' ? 'Note by AI, verified' : 'Note by template'}
          </Badge>
          <Badge tone="review">{q.status}</Badge>
        </div>
      </div>

      <details className="group mt-3 text-xs text-muted">
        <summary className="cursor-pointer list-none select-none hover:text-ink">
          <span className="inline-block transition-transform group-open:rotate-90">›</span> Facts from code
          {t?.proposed_account && ' and proposed account'}
        </summary>
        <p className="mt-2 rounded-xl bg-card px-3 py-2 font-mono text-[12px] leading-relaxed ring-1 ring-line">{q.facts}</p>
        {t?.proposed_account && <p className="mt-2">Proposed account: {t.proposed_account}</p>}
      </details>
    </article>
  )
}
