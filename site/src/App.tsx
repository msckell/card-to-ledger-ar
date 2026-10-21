import { marked } from 'marked'
import { useEffect } from 'react'
import { site } from './data'
import HowItWorks from './HowItWorks'
import Journal from './Journal'
import Overview from './Overview'
import Queue from './Queue'
import RulesOrAI from './RulesOrAI'
import { Section } from './ui'

// Shown only once the repository is public.
const REPO_URL = ''

const NAV = [
  ['overview', 'Overview'],
  ['queue', 'Review queue'],
  ['journal', 'Journal entry'],
  ['rules-or-ai', 'Rules or AI?'],
  ['how', 'How it works'],
  ['memo', 'Memo'],
] as const

export default function App() {
  // The page renders after load, so a link with #section needs a nudge to land on it.
  useEffect(() => {
    if (window.location.hash) document.getElementById(window.location.hash.slice(1))?.scrollIntoView()
  }, [])
  return (
    <>
      <header className="sticky top-0 z-10 border-b border-line bg-paper/90 backdrop-blur">
        <nav className="mx-auto flex max-w-5xl items-center gap-5 overflow-x-auto px-4 py-3 text-sm">
          <a href="#overview" className="shrink-0 font-serif font-semibold">
            Card to Ledger AR
          </a>
          {NAV.slice(1).map(([id, label]) => (
            <a key={id} href={`#${id}`} className="shrink-0 text-muted hover:text-ink">
              {label}
            </a>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-5xl px-4">
        <Overview />
        <Queue />
        <Journal />
        <RulesOrAI />
        <HowItWorks repoUrl={REPO_URL} />
        {site.memo && (
          <Section id="memo" eyebrow="6 · Product memo" title="What I would ship first">
            <article
              className="prose-memo max-w-2xl rounded-lg border border-line bg-card p-5 sm:p-8"
              dangerouslySetInnerHTML={{ __html: marked.parse(site.memo, { async: false }) as string }}
            />
          </Section>
        )}
      </main>
      <footer className="mt-8 border-t border-line">
        <div className="mx-auto max-w-5xl px-4 py-8 text-sm text-muted">
          <p>
            Máximo Sckell ·{' '}
            <a className="underline underline-offset-2" href="https://www.linkedin.com/in/msckell" target="_blank" rel="noreferrer">
              linkedin.com/in/msckell
            </a>{' '}
            ·{' '}
            <a className="underline underline-offset-2" href="https://github.com/msckell" target="_blank" rel="noreferrer">
              github.com/msckell
            </a>
          </p>
          <p className="mt-2 text-xs text-faint">
            Independent prototype. Not affiliated with Jeeves. Fictional company and synthetic transactions. Exchange rates
            from a public source. Taxes out of scope.
          </p>
        </div>
      </footer>
    </>
  )
}
