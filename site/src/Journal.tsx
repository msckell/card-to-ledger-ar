import { site } from './data'
import { Arrow, ButtonLink, Check, Section } from './ui'

const SHEETS = ['Resumen', 'Asiento', 'Movimientos', 'Excepciones', 'Metodología']

export default function Journal() {
  const j = site.journal
  return (
    <Section
      id="journal"
      eyebrow="The deliverable"
      title={`The ${site.meta.period_label} entry, in pesos, ready to post.`}
      intro={
        <>
          One summary entry built from {j.lines} audited lines. Each movement is valued at the official seller rate of its
          posting day. The USDC account and the card payable are remeasured at the closing rate of{' '}
          {site.summary.closing_rate}. Items still in review sit in Partidas pendientes de imputación.
        </>
      }
    >
      <div className="grid gap-5 lg:grid-cols-[1.6fr_1fr]">
        <div className="overflow-hidden rounded-3xl border border-line">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-paper text-left text-[11px] uppercase tracking-[0.14em] text-faint">
                <th className="px-4 py-3 font-semibold sm:px-6">Cuenta</th>
                <th className="hidden px-3 py-3 text-right font-semibold sm:table-cell">Debe</th>
                <th className="hidden px-4 py-3 text-right font-semibold sm:table-cell sm:px-6">Haber</th>
              </tr>
            </thead>
            <tbody>
              {j.rows.map((r) => (
                <tr key={r.account} className="border-b border-line last:border-0">
                  <td className="px-4 py-2.5 sm:px-6">
                    <span className="block leading-snug">{r.name}</span>
                    <span className="font-mono text-[11px] text-faint">{r.account}</span>
                    <span className="num mt-0.5 block text-[13px] sm:hidden">
                      {r.debe ? <>Debe {r.debe}</> : <span className="text-muted">Haber {r.haber}</span>}
                    </span>
                  </td>
                  <td className="num hidden px-3 py-2.5 text-right align-top sm:table-cell">{r.debe}</td>
                  <td className="num hidden px-4 py-2.5 text-right align-top sm:table-cell sm:px-6">{r.haber}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="bg-night font-semibold text-on-night">
                <td className="px-4 py-3.5 sm:px-6">
                  Totales ARS
                  <span className="num block text-[13px] font-medium text-gold-light sm:hidden">
                    Debe {j.totals.debe} · Haber {j.totals.haber}
                  </span>
                </td>
                <td className="num hidden px-3 py-3.5 text-right text-gold-light sm:table-cell">{j.totals.debe}</td>
                <td className="num hidden px-4 py-3.5 text-right text-gold-light sm:table-cell sm:px-6">{j.totals.haber}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div className="flex flex-col gap-5 lg:sticky lg:top-24 lg:self-start">
          <div className="rounded-3xl border border-line bg-card p-6">
            <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-gold-text">
              <Check className="h-4 w-4" /> {j.totals.balanced ? 'Balanced to the cent' : 'Not balanced'}
            </p>
            <div className="mt-4 space-y-1">
              <p className="text-xs text-faint">Debe</p>
              <p className="num text-2xl font-semibold">ARS {j.totals.debe}</p>
              <p className="py-1 text-xl font-semibold text-gold-text" aria-hidden>
                =
              </p>
              <p className="text-xs text-faint">Haber</p>
              <p className="num text-2xl font-semibold">ARS {j.totals.haber}</p>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-muted">
              The build stops if debits and credits differ by a single cent. Every line keeps its audit trail: the rule or AI
              suggestion behind it, its status, and who approved it.
            </p>
          </div>

          <div className="rounded-3xl bg-night p-6 text-on-night">
            <p className="text-lg font-semibold">The whole close, in one Excel file</p>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {SHEETS.map((s) => (
                <span key={s} className="rounded-md bg-night-2 px-2 py-1 text-xs text-on-night-muted ring-1 ring-night-line">
                  {s}
                </span>
              ))}
            </div>
            <div className="mt-5">
              <ButtonLink href={j.excel} download>
                Download the Excel <Arrow className="rotate-90" />
              </ButtonLink>
            </div>
          </div>
        </div>
      </div>
    </Section>
  )
}
