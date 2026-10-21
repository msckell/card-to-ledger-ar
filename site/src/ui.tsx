import type { ReactNode } from 'react'

export type Tone = 'white' | 'paper' | 'night'

const SURFACE: Record<Tone, string> = {
  white: 'bg-card text-ink',
  paper: 'bg-paper text-ink',
  night: 'bg-night text-on-night',
}

/** Full bleed band with a centered column. The short gold rule above the title is the page's signature. */
export function Section({ id, eyebrow, title, intro, tone = 'white', children }: {
  id?: string
  eyebrow: string
  title: ReactNode
  intro?: ReactNode
  tone?: Tone
  children: ReactNode
}) {
  const night = tone === 'night'
  return (
    <section id={id} className={SURFACE[tone]}>
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24">
        <GoldRule />
        <p className={`mt-5 text-xs font-semibold uppercase tracking-[0.22em] ${night ? 'text-gold-light' : 'text-gold-text'}`}>
          {eyebrow}
        </p>
        <h2 className="mt-3 max-w-3xl text-3xl font-semibold leading-[1.15] tracking-tight sm:text-[2.6rem]">{title}</h2>
        {intro && (
          <div className={`mt-4 max-w-2xl text-base leading-relaxed sm:text-[17px] ${night ? 'text-on-night-muted' : 'text-muted'}`}>
            {intro}
          </div>
        )}
        <div className="mt-10 sm:mt-14">{children}</div>
      </div>
    </section>
  )
}

export function GoldRule({ className = '' }: { className?: string }) {
  return <div className={`h-px w-24 bg-gradient-to-r from-gold via-gold-light to-transparent ${className}`} aria-hidden />
}

export function Eyebrow({ children, night = false }: { children: ReactNode; night?: boolean }) {
  return (
    <p className={`text-[11px] font-semibold uppercase tracking-[0.2em] ${night ? 'text-on-night-muted' : 'text-faint'}`}>
      {children}
    </p>
  )
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-2xl border border-line bg-card ${className}`}>{children}</div>
}

export type Who = 'rules' | 'ai' | 'review'

export const WHO: Record<Who, { label: string; dot: string; bar: string; barNight: string; text: string }> = {
  rules: { label: 'Rules', dot: 'bg-rules', bar: 'bg-rules', barNight: 'bg-rules-night', text: 'text-rules' },
  ai: { label: 'AI', dot: 'bg-ai', bar: 'bg-ai', barNight: 'bg-ai', text: 'text-gold-text' },
  review: { label: 'A person', dot: 'bg-review', bar: 'bg-review stripes', barNight: 'bg-review-night stripes', text: 'text-review' },
}

const TONES = {
  rules: 'bg-[#ececea] text-rules',
  ai: 'bg-gold-soft text-gold-text',
  review: 'bg-review-soft text-review',
  neutral: 'bg-paper text-muted ring-1 ring-line',
  night: 'bg-night-2 text-on-night-muted ring-1 ring-night-line',
  gold: 'bg-gold/15 text-gold-light ring-1 ring-gold/30',
} as const

export function Badge({ tone = 'neutral', children }: { tone?: keyof typeof TONES; children: ReactNode }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider ${TONES[tone]}`}>
      {children}
    </span>
  )
}

export function Dot({ who, night = false }: { who: Who; night?: boolean }) {
  const c = who === 'rules' && night ? 'bg-rules-night' : who === 'review' && night ? 'bg-review-night' : WHO[who].dot
  return <span className={`inline-block h-2.5 w-2.5 shrink-0 rounded-full ${c}`} aria-hidden />
}

export function ButtonLink({ href, children, variant = 'gold', download }: {
  href: string
  children: ReactNode
  variant?: 'gold' | 'light' | 'dark' | 'outline'
  download?: boolean
}) {
  const v = {
    gold: 'bg-gold text-night hover:bg-gold-light',
    light: 'rounded-full bg-on-night text-night hover:bg-white',
    dark: 'bg-night text-on-night hover:bg-night-2',
    outline: 'rounded-full border border-night-line text-on-night hover:border-gold',
  }[variant]
  return (
    <a
      href={href}
      download={download}
      className={`inline-flex items-center gap-2 rounded-lg px-5 py-3 text-sm font-semibold transition-colors ${v}`}
    >
      {children}
    </a>
  )
}

export function Arrow({ className = '' }: { className?: string }) {
  return (
    <svg viewBox="0 0 16 16" className={`h-4 w-4 ${className}`} fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
      <path d="M3 8h10M9 4l4 4-4 4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function Check({ className = '' }: { className?: string }) {
  return (
    <svg viewBox="0 0 16 16" className={`h-4 w-4 ${className}`} fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
      <path d="M3.5 8.5l3 3 6-7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

/** Renders [TX-0042] style citations as small ID chips. */
export function Cited({ text }: { text: string }) {
  const parts = text.split(/(\[[A-Z]+-[A-Z0-9]+\])/g)
  return (
    <>
      {parts.map((p, i) =>
        /^\[[A-Z]+-[A-Z0-9]+\]$/.test(p) ? (
          <code key={i} className="rounded bg-paper px-1 py-px font-mono text-[12px] text-ink ring-1 ring-line">
            {p.slice(1, -1)}
          </code>
        ) : (
          <span key={i}>{p}</span>
        ),
      )}
    </>
  )
}

export function Mono({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <span className={`font-mono text-[12px] ${className}`}>{children}</span>
}
