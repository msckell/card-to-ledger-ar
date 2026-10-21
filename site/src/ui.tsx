import type { ReactNode } from 'react'

export function Section({ id, eyebrow, title, intro, children }: {
  id: string
  eyebrow: string
  title: string
  intro?: ReactNode
  children: ReactNode
}) {
  return (
    <section id={id} className="border-t border-line py-12 sm:py-16">
      <p className="text-xs font-medium uppercase tracking-[0.14em] text-faint">{eyebrow}</p>
      <h2 className="mt-2 font-serif text-2xl font-semibold sm:text-3xl">{title}</h2>
      {intro && <div className="mt-3 max-w-2xl text-[15px] leading-relaxed text-muted">{intro}</div>}
      <div className="mt-8">{children}</div>
    </section>
  )
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-lg border border-line bg-card ${className}`}>{children}</div>
}

const TONES = {
  rules: 'bg-accent-soft text-rules',
  ai: 'bg-ai-soft text-ai',
  review: 'bg-review-soft text-review',
  neutral: 'bg-paper text-muted border border-line',
} as const

export function Badge({ tone = 'neutral', children }: { tone?: keyof typeof TONES; children: ReactNode }) {
  return (
    <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[11px] font-medium uppercase tracking-wide ${TONES[tone]}`}>
      {children}
    </span>
  )
}

/** Renders [TX-0042] style citations as small ID chips. */
export function Cited({ text }: { text: string }) {
  const parts = text.split(/(\[[A-Z]+-[A-Z0-9]+\])/g)
  return (
    <>
      {parts.map((p, i) =>
        /^\[[A-Z]+-[A-Z0-9]+\]$/.test(p) ? (
          <code key={i} className="rounded bg-paper px-1 py-px font-mono text-[12px] text-ink">
            {p.slice(1, -1)}
          </code>
        ) : (
          <span key={i}>{p}</span>
        ),
      )}
    </>
  )
}

export function Stat({ label, value, sub, tone }: { label: string; value: ReactNode; sub?: ReactNode; tone?: 'rules' | 'ai' | 'review' }) {
  const color = tone === 'rules' ? 'text-rules' : tone === 'ai' ? 'text-ai' : tone === 'review' ? 'text-review' : 'text-ink'
  return (
    <Card className="p-4">
      <p className="text-xs text-muted">{label}</p>
      <p className={`num mt-1 break-words font-serif text-xl font-semibold sm:text-2xl ${color}`}>{value}</p>
      {sub && <p className="mt-1 text-xs text-faint">{sub}</p>}
    </Card>
  )
}
