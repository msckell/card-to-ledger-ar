import { site } from './data'
import { Badge, Section } from './ui'

const LABEL_TONE: Record<string, 'rules' | 'ai' | 'review' | 'neutral'> = {
  documented: 'rules',
  assumption: 'ai',
  'out of scope': 'neutral',
}

const ORDER = ['documented', 'assumption', 'out of scope']

export default function Methodology({ repoUrl }: { repoUrl: string }) {
  const m = site.methodology
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

      <div className="mt-6 divide-y divide-line overflow-hidden rounded-3xl border border-line bg-card">
        {m.map((x) => (
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
