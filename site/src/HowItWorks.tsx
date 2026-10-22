import type { ReactNode } from 'react'
import { pct, site } from './data'
import Examples from './Examples'
import { Badge, Section, type Who } from './ui'

type Step = { title: string; body: string; who: Who | 'input' | 'output'; tag: string; icon: ReactNode }

const STEPS: Step[] = [
  {
    title: 'Export and receipts',
    body: 'Card and USDC movements in an assumed export format, plus receipt PDFs that are not linked to anything.',
    who: 'input',
    tag: 'Input',
    icon: <path d="M5 3h7l3 3v11H5zM12 3v3h3" />,
  },
  {
    title: 'Rules',
    body: 'Exchange rate, receipt matching, duplicate, missing receipt, mismatch and refund checks, and accounts for known merchants.',
    who: 'rules',
    tag: 'Code',
    icon: <path d="M4 6h12M4 10h12M4 14h7" />,
  },
  {
    title: 'AI, three uses',
    body: 'Reads receipts. Suggests an account when no rule applies. Explains each exception in plain English.',
    who: 'ai',
    tag: 'AI',
    icon: <path d="M10 3l1.6 4.4L16 9l-4.4 1.6L10 15l-1.6-4.4L4 9l4.4-1.6z" />,
  },
  {
    title: 'Verifier',
    body: 'Code checks every amount the AI read against the charge, and rejects notes with figures, invented IDs or claims.',
    who: 'rules',
    tag: 'Code',
    icon: <path d="M10 3l6 2.5v4.5c0 3.5-2.6 6-6 7-3.4-1-6-3.5-6-7V5.5zM7.5 10l2 2 3.5-4" />,
  },
  {
    title: 'Review queue',
    body: 'Everything with an open question waits for a person, with its evidence next to it.',
    who: 'review',
    tag: 'Person',
    icon: <path d="M10 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM4 17c.8-3 3.2-5 6-5s5.2 2 6 5" />,
  },
  {
    title: 'Journal entry',
    body: 'A balanced summary entry in ARS with an audit trail per line, delivered as Excel.',
    who: 'output',
    tag: 'Output',
    icon: <path d="M4 4h12v12H4zM4 8h12M9 8v8" />,
  },
]

const NODE: Record<Step['who'], string> = {
  input: 'bg-paper text-ink ring-1 ring-line',
  rules: 'bg-rules text-white',
  ai: 'bg-ai text-night',
  review: 'bg-review text-white',
  output: 'bg-night text-gold',
}

export default function HowItWorks() {
  const e = site.eval
  const ex = e.explanations
  const uses = [
    {
      title: 'Read receipts',
      stat: pct(e.extraction.ai?.all_fields),
      note: `of ${e.extraction.receipts} receipts with vendor, date, amount and currency all right`,
      guard: 'Code compares every amount it reads with the charge. A mismatch becomes an exception, never a silent fix.',
    },
    {
      title: 'Suggest an account',
      stat: e.threshold.recommended_row ? pct(e.threshold.recommended_row.accuracy) : pct(e.ai_accounts?.accuracy),
      note: e.threshold.recommended_row
        ? `right on the ${e.threshold.recommended_row.accepted} suggestions accepted at confidence ${e.threshold.recommended} or more`
        : 'right across all suggestions',
      guard: 'Only for merchants no rule covers, only from the allowed accounts. Below the threshold a person decides.',
    },
    {
      title: 'Explain exceptions',
      stat: ex ? `${ex.accepted_first_try + ex.accepted_after_retry}/${ex.exceptions}` : 'n/a',
      note: 'explanations passed the verifier',
      guard: 'The AI never types a number. Figures come from code, and a note that still fails after two retries falls back to a template.',
    },
  ]

  return (
    <Section
      id="how"
      eyebrow="How it works"
      title="Code does everything it can. AI fills three gaps. A person decides the rest."
      intro="All AI calls happen when the data is built, never when this page loads. Each one is measured against the correct answer."
    >
      <ol className="relative grid gap-3 lg:grid-cols-6 lg:gap-4">
        <div className="absolute bottom-6 left-6 top-6 w-px bg-gradient-to-b from-gold/60 to-gold/10 lg:bottom-auto lg:right-12 lg:h-px lg:w-auto lg:bg-gradient-to-r" aria-hidden />
        {STEPS.map((s, i) => (
          <li key={s.title} className="relative flex gap-4 lg:flex-col lg:gap-3">
            <span className={`relative z-10 flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl ${NODE[s.who]}`}>
              <svg viewBox="0 0 20 20" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                {s.icon}
              </svg>
            </span>
            <div className="pb-2">
              <p className="num text-xs text-faint">{String(i + 1).padStart(2, '0')}</p>
              <p className="font-semibold">{s.title}</p>
              <p className="mt-1 text-sm leading-relaxed text-muted">{s.body}</p>
              <p className="mt-2">
                <Badge tone={s.who === 'rules' ? 'rules' : s.who === 'ai' ? 'ai' : s.who === 'review' ? 'review' : 'neutral'}>{s.tag}</Badge>
              </p>
            </div>
          </li>
        ))}
      </ol>

      <Examples />

      <div className="mt-16 rounded-3xl bg-night p-6 text-on-night sm:p-10">
        <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-gold-light">AI is used in exactly three places</p>
        <p className="mt-3 max-w-2xl text-2xl font-semibold leading-snug sm:text-3xl">Each one has a guardrail made of code, and a score.</p>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {uses.map((u, i) => (
            <div key={u.title} className="rounded-2xl border border-night-line bg-night-2 p-5">
              <p className="text-sm font-semibold">
                <span className="num text-gold">{i + 1}.</span> {u.title}
              </p>
              <p className="num mt-4 text-4xl font-semibold text-gold-light">{u.stat}</p>
              <p className="mt-1 text-xs leading-relaxed text-on-night-muted">{u.note}</p>
              <p className="mt-4 border-t border-night-line pt-4 text-sm leading-relaxed text-on-night-muted">{u.guard}</p>
            </div>
          ))}
        </div>
      </div>
    </Section>
  )
}
