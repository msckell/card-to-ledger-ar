import { site } from './data'
import { Badge, Card, Section } from './ui'

export default function Journal() {
  const j = site.journal
  return (
    <Section
      id="journal"
      eyebrow="3 · Journal entry"
      title="The September entry, in pesos"
      intro={
        <>
          One summary entry for {site.meta.period_label}, built from {j.lines} audited lines. Each movement is valued at
          the official seller rate of its posting day. The USDC account and the card payable are remeasured at the
          closing rate of {j.balances.closing_rate}. Items still in review sit in Partidas pendientes de imputación.
        </>
      }
    >
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[520px] text-sm">
            <thead>
              <tr className="border-b border-line bg-paper text-left text-xs uppercase tracking-wide text-muted">
                <th className="px-4 py-2.5 font-medium">Cuenta</th>
                <th className="px-4 py-2.5 font-medium">Nombre</th>
                <th className="px-4 py-2.5 text-right font-medium">Debe (ARS)</th>
                <th className="px-4 py-2.5 text-right font-medium">Haber (ARS)</th>
              </tr>
            </thead>
            <tbody>
              {j.rows.map((r) => (
                <tr key={r.account} className="border-b border-line last:border-0">
                  <td className="px-4 py-2 font-mono text-xs text-muted">{r.account}</td>
                  <td className="px-4 py-2">{r.name}</td>
                  <td className="num px-4 py-2 text-right">{r.debe}</td>
                  <td className="num px-4 py-2 text-right">{r.haber}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t-2 border-ink font-semibold">
                <td className="px-4 py-2.5" />
                <td className="px-4 py-2.5">Totales</td>
                <td className="num px-4 py-2.5 text-right">{j.totals.debe}</td>
                <td className="num px-4 py-2.5 text-right">{j.totals.haber}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </Card>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <Badge tone={j.totals.balanced ? 'rules' : 'review'}>
          {j.totals.balanced ? 'Balanced: Debe equals Haber' : 'Not balanced'}
        </Badge>
        <a
          href={j.excel}
          download
          className="inline-flex items-center gap-2 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90"
        >
          Download the Excel
        </a>
        <span className="text-xs text-faint">Sheets: Resumen · Asiento · Movimientos · Excepciones · Metodología</span>
      </div>
      <p className="mt-4 max-w-2xl text-sm text-muted">
        The build stops if debits and credits differ by a single cent. Every line keeps its audit trail: the rule ID or AI
        suggestion ID behind it, its status, and who approved it.
      </p>
    </Section>
  )
}
