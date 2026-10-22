import { useEffect } from 'react'
import { site } from './data'
import Flow from './Flow'
import Hero from './Hero'
import HowItWorks from './HowItWorks'
import Journal from './Journal'
import Memo from './Memo'
import Methodology from './Methodology'
import Problem from './Problem'
import Queue from './Queue'
import RulesOrAI from './RulesOrAI'
import { Arrow, ButtonLink } from './ui'

// Shown only once the repository is public.
const REPO_URL = ''

const NAV = [
  ['results', 'Results'],
  ['how', 'How it works'],
  ['rules-or-ai', 'Rules or AI?'],
  ['queue', 'Review'],
  ['memo', 'Memo'],
] as const

export default function App() {
  // The page renders after load, so a link with #section needs a nudge to land on it.
  useEffect(() => {
    if (window.location.hash) document.getElementById(window.location.hash.slice(1))?.scrollIntoView()
  }, [])
  return (
    <>
      <header className="sticky top-0 z-20 border-b border-night-line bg-night/90 text-on-night backdrop-blur">
        <nav className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-4 py-3 sm:px-6">
          <a href="#top" className="flex shrink-0 items-center gap-2.5 font-semibold tracking-tight">
            <Mark />
            Card to Ledger AR
          </a>
          <div className="hidden items-center gap-6 text-sm text-on-night-muted md:flex">
            {NAV.map(([id, label]) => (
              <a key={id} href={`#${id}`} className="transition-colors hover:text-gold-light">
                {label}
              </a>
            ))}
          </div>
          <a
            href={site.journal.excel}
            download
            className="shrink-0 rounded-full bg-on-night px-4 py-2 text-xs font-semibold text-night transition-colors hover:bg-white sm:text-sm"
          >
            Download Excel
          </a>
        </nav>
      </header>

      <main>
        <Hero />
        <Problem />
        <Flow />
        <HowItWorks />
        <RulesOrAI />
        <Queue />
        <Journal />
        <Methodology repoUrl={REPO_URL} />
        <Memo />
      </main>

      <footer className="bg-night text-on-night">
        <div className="mx-auto max-w-6xl px-4 pt-20 sm:px-6 sm:pt-28">
          <div className="h-px w-24 bg-gradient-to-r from-gold via-gold-light to-transparent" aria-hidden />
          <p className="mt-6 max-w-3xl text-3xl font-semibold leading-tight tracking-tight sm:text-5xl">
            Happy to walk you through it.
          </p>
          <p className="mt-4 max-w-xl text-on-night-muted">
            {site.meta.subtitle} by {site.meta.author}. The rules, the AI steps and every number on this page come from
            one reproducible build.
          </p>
          <div className="mt-8">
            <ButtonLink href="https://www.linkedin.com/in/msckell" newTab>
              Talk on LinkedIn <Arrow />
            </ButtonLink>
          </div>
        </div>
        <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
          <div className="flex flex-wrap items-center justify-between gap-6">
            <p className="flex items-center gap-2.5 font-semibold">
              <Mark /> Card to Ledger AR
            </p>
            <ButtonLink href="#top" variant="outline">
              Back to top
            </ButtonLink>
          </div>
          <div className="mt-8 h-px bg-night-line" />
          <p className="mt-8 text-sm text-gold-light">
            Máximo Sckell ·{' '}
            <a className="underline underline-offset-4 hover:text-gold" href="https://www.linkedin.com/in/msckell" target="_blank" rel="noreferrer">
              linkedin.com/in/msckell
            </a>{' '}
            ·{' '}
            <a className="underline underline-offset-4 hover:text-gold" href="https://github.com/msckell" target="_blank" rel="noreferrer">
              github.com/msckell
            </a>
          </p>
          <p className="mt-3 max-w-3xl text-xs leading-relaxed text-on-night-muted">
            Independent prototype. Not affiliated with Jeeves. Fictional company and synthetic transactions. Exchange rates
            from a public source. Taxes out of scope.
          </p>
        </div>
      </footer>
    </>
  )
}

/** The product mark: three ledger lines in gold. */
function Mark() {
  return (
    <svg viewBox="0 0 32 32" className="h-7 w-7" aria-hidden>
      <rect width="32" height="32" rx="8" fill="#161617" stroke="#2a2a2c" />
      <path d="M9 11h14M9 16h14M9 21h9" stroke="#c29a45" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  )
}
