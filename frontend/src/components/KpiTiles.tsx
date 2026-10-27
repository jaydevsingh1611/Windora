import type { Analysis } from '../api'
import { gw, pct, signedGw } from '../format'

export function KpiTiles({ analysis }: { analysis: Analysis }) {
  const s = analysis.summary
  const [hLo, hHi] = analysis.horizonRange ?? [0, 0]
  const tiles = [
    {
      label: 'Typical miss (MAE)',
      value: gw(s.mae),
      note: `${pct(s.maePctOfMeanActual)} of average wind output`,
    },
    {
      label: 'Bias',
      value: signedGw(s.bias),
      note:
        s.bias >= 0
          ? `Over-forecast in ${pct(100 * s.shareOverForecast)} of hours`
          : `Under-forecast in ${pct(100 * (1 - s.shareOverForecast))} of hours`,
    },
    {
      label: 'P90 shortfall cover',
      value: gw(s.shortfallCoverP90),
      note: 'Extra MW that covered 90% of hours',
      emphasis: true,
    },
    {
      label: 'RMSE',
      value: gw(s.rmse),
      note: `Worst hour off by ${gw(s.maxAbsError, 1)}`,
    },
    {
      label: 'Forecast lead time',
      value: `${Math.round(hLo)}–${Math.round(hHi)}h`,
      note: `${analysis.runsUsed} forecast runs, ${s.count} hours scored`,
    },
  ]
  return (
    <section className="kpis" aria-label="Forecast accuracy summary">
      {tiles.map((t) => (
        <div key={t.label} className={`kpi${t.emphasis ? ' emphasis' : ''}`}>
          <div className="kpi-label">{t.label}</div>
          <div className="kpi-value">{t.value}</div>
          <div className="kpi-note">{t.note}</div>
        </div>
      ))}
    </section>
  )
}
