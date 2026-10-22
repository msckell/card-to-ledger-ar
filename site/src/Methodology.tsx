import { site } from './data'
import { Badge, Section } from './ui'

const LABEL_TONE: Record<string, 'rules' | 'ai' | 'review' | 'neutral'> = {
  documented: 'rules',
  assumption: 'ai',
  'out of scope': 'neutral',
}

const ORDER = ['documented', 'assumption', 'out of scope']

// The choices that move the numbers most, shown open. The rest stay folded.
const KEY = ['Which rate and which day', 'USDC valuation', 'Taxes', 'Company and transactions']

export default function Methodology({ repoUrl }: { repoUrl: string }) {
  const m = site.methodology
  const key = KEY.map((t) => m.find((x) => x.topic === t)).filter((x) => x !== undefined)
  const rest = m.filter((x) => !KEY.includes(x.topic))
  const counts = ORDER.map((l) => ({ label: l, n: m.filter((x) => x.label === l).length })).filter((c) => c.n > 0)
  return (
    <Section
      id="methodology"
      eyebrow="Methodology"
      title="Every choice behind the numbers, labeled."
      intro="Documented means it rests on a cited source. Assumption means it is a choice to validate with an accountant. The same list is in the Excel, on its methodology sheet."
    >
      <div className="flex flex-wrap gap-3">
        {counts.map((c) => (
          <div key={c.label} className="rounded-2xl bg-card px-5 py-4 ring-1 ring-line">
            <p className="num text-2xl font-semibold">{c.n}</p>
            <Badge tone={LABEL_TONE[c.label] ?? 'neutral'}>{c.label}</Badge>
          </div>
        ))}
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        {key.map((x) => (
          <div key={x.topic} className="rounded-2xl bg-paper p-5 ring-1 ring-line">
            <div className="flex items-start justify-between gap-3">
              <p className="font-semibold">{x.topic}</p>
              <Badge tone={LABEL_TONE[x.label] ?? 'neutral'}>{x.label}</Badge>
            </div>
            <p className="mt-2 text-sm leading-relaxed text-muted [overflow-wrap:anywhere]">{x.detail}</p>
          </div>
        ))}
      </div>

      <p className="mt-8 text-[11px] font-semibold uppercase tracking-[0.2em] text-faint">Every other choice</p>
      <div className="mt-3 divide-y divide-line overflow-hidden rounded-3xl border border-line bg-card">
        {rest.map((x) => (
          <details key={x.topic} className="group px-5 py-4 sm:px-6">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3">
              <span className="flex items-center gap-2 text-sm font-semibold">
                <span className="inline-block text-faint transition-transform group-open:rotate-90">›</span> {x.topic}
              </span>
              <Badge tone={LABEL_TONE[x.label] ?? 'neutral'}>{x.label}</Badge>
            </summary>
            <p className="mt-2 pl-5 text-sm leading-relaxed text-muted [overflow-wrap:anywhere]">{x.detail}</p>
          </details>
        ))}
      </div>

      <p className="mt-5 text-xs text-faint">
        Exchange rates downloaded {site.meta.fx_downloaded} from{' '}
        <a className="underline underline-offset-2" href={site.meta.fx_source} target="_blank" rel="noreferrer">
          ArgentinaDatos
        </a>
        , frozen in the repository so the build is reproducible. Taxes are out of scope.
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
