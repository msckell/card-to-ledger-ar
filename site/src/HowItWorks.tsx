import { site } from './data'
import { Badge, Card, Section } from './ui'

const STEPS = [
  { title: 'Export and receipts', body: 'Card and USDC movements in an assumed export format, plus receipt PDFs that are not linked to anything.', tone: 'neutral' },
  { title: 'Rules', body: 'Exchange rate, receipt matching, duplicate, missing receipt, mismatch and refund checks, and account rules for known merchants.', tone: 'rules' },
  { title: 'AI, three uses', body: 'Reads receipts. Suggests an account when no rule applies. Explains each exception in plain English.', tone: 'ai' },
  { title: 'Verifier', body: 'Code checks every amount the AI read against the charge, and rejects explanations with figures, invented IDs or claims.', tone: 'rules' },
  { title: 'Review queue', body: 'Everything with an open question waits for a person, with its evidence next to it.', tone: 'review' },
  { title: 'Journal entry', body: 'Balanced summary entry in ARS with an audit trail per line, delivered as Excel.', tone: 'rules' },
] as const

const LABEL_TONE: Record<string, 'rules' | 'ai' | 'review' | 'neutral'> = {
  documented: 'rules',
  assumption: 'review',
  'out of scope': 'neutral',
}

export default function HowItWorks({ repoUrl }: { repoUrl: string }) {
  return (
    <Section
      id="how"
      eyebrow="5 · How it works"
      title="From export to entry"
      intro="Deterministic code does everything it can. AI handles only what rules cannot, and a person reviews the rest. All AI calls happen when the data is built, never when this page loads."
    >
      <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {STEPS.map((s, i) => (
          <li key={s.title}>
            <Card className="h-full p-4">
              <div className="flex items-center gap-2">
                <span className="num flex h-6 w-6 items-center justify-center rounded-full bg-ink text-xs text-white">{i + 1}</span>
                <span className="font-semibold">{s.title}</span>
                {s.tone !== 'neutral' && (
                  <Badge tone={s.tone}>{s.tone === 'rules' ? 'Code' : s.tone === 'ai' ? 'AI' : 'Person'}</Badge>
                )}
              </div>
              <p className="mt-2 text-sm text-muted">{s.body}</p>
            </Card>
          </li>
        ))}
      </ol>

      <h3 className="mt-12 font-serif text-xl font-semibold">Methodology</h3>
      <p className="mt-1 text-sm text-muted">Every choice behind the numbers, labeled. The same list is in the Excel.</p>
      <div className="mt-4 divide-y divide-line rounded-lg border border-line bg-card">
        {site.methodology.map((m) => (
          <div key={m.topic} className="grid grid-cols-1 gap-1 px-4 py-3 sm:grid-cols-[220px_110px_minmax(0,1fr)] sm:gap-4">
            <p className="text-sm font-medium">{m.topic}</p>
            <p>
              <Badge tone={LABEL_TONE[m.label] ?? 'neutral'}>{m.label}</Badge>
            </p>
            <p className="min-w-0 text-sm text-muted [overflow-wrap:anywhere]">{m.detail}</p>
          </div>
        ))}
      </div>
      <p className="mt-4 text-xs text-faint">
        Exchange rates downloaded {site.meta.fx_downloaded} from{' '}
        <a className="underline underline-offset-2" href={site.meta.fx_source} target="_blank" rel="noreferrer">
          ArgentinaDatos
        </a>
        , frozen in the repository so the build is reproducible.
        {repoUrl && (
          <>
            {' '}Source code:{' '}
            <a className="underline underline-offset-2" href={repoUrl} target="_blank" rel="noreferrer">
              {repoUrl.replace('https://', '')}
            </a>
            .
          </>
        )}
      </p>
    </Section>
  )
}
