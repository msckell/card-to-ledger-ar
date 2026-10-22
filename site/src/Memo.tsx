import { marked } from 'marked'
import { useState } from 'react'
import { site } from './data'
import { Arrow, Section } from './ui'

const TEASER = 'How to ship it'

function sections(md: string) {
  return md
    .split(/^## /m)
    .slice(1)
    .map((chunk) => {
      const [heading, ...rest] = chunk.split('\n')
      return { heading: heading.trim(), body: rest.join('\n').trim() }
    })
}

export default function Memo() {
  const [open, setOpen] = useState(false)
  if (!site.memo) return null
  const parts = sections(site.memo)
  const teaser = parts.find((p) => p.heading === TEASER)
  const html = (md: string) => ({ __html: marked.parse(md, { async: false }) as string })

  return (
    <Section
      id="memo"
      tone="paper"
      eyebrow="Product memo"
      title="What I would ship first."
      intro="A short memo for the product team. Every number in it is filled in at build time from the same data as this page."
    >
      <div className="grid gap-8 lg:grid-cols-[1fr_2fr]">
        <nav aria-label="Memo sections">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-faint">Inside the memo</p>
          <ol className="mt-4 space-y-2 border-l border-line pl-4 text-sm">
            {parts.map((p, i) => (
              <li key={p.heading} className={p.heading === TEASER ? 'font-semibold text-gold-text' : 'text-muted'}>
                <span className="num text-faint">{String(i + 1).padStart(2, '0')}</span> {p.heading}
              </li>
            ))}
          </ol>
        </nav>

        <div>
          {!open && teaser && (
            <article className="prose-memo rounded-3xl border border-line bg-card p-6 sm:p-8">
              <h2>{teaser.heading}</h2>
              <div dangerouslySetInnerHTML={html(teaser.body)} />
            </article>
          )}
          {open && (
            <article className="prose-memo rounded-3xl border border-line bg-card p-6 sm:p-8" dangerouslySetInnerHTML={html(site.memo)} />
          )}
          <button
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            className="mt-5 inline-flex items-center gap-2 rounded-lg bg-night px-5 py-3 text-sm font-semibold text-on-night hover:bg-night-2"
          >
            {open ? 'Show the short version' : 'Read the full memo'} <Arrow className={open ? '-rotate-90' : 'rotate-90'} />
          </button>
        </div>
      </div>
    </Section>
  )
}
