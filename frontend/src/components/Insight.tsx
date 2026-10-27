import type { Analysis, Query } from '../api'
import { gw, pct, weekdayDay } from '../format'

/** Plain-English headline a trader can act on. */
export function Insight({ analysis, query }: { analysis: Analysis; query: Query }) {
  const s = analysis.summary
  const basis =
    query.mode === 'gate'
      ? `the latest forecast available at ${query.gate} the day before delivery`
      : `the latest forecast made at least ${query.horizon}h ahead`
  const direction = s.bias >= 0 ? 'over-estimated' : 'under-estimated'
  return (
    <section className="insight">
      <p>
        Between <strong>{weekdayDay(query.start)}</strong> and <strong>{weekdayDay(query.end)}</strong>, {basis}{' '}
        missed actual wind output by <strong>{gw(s.mae)}</strong> per hour on average (
        {pct(s.maePctOfMeanActual)} of output). It typically <strong>{direction}</strong> wind by{' '}
        <strong>{gw(Math.abs(s.bias))}</strong>.
      </p>
      <p>
        Buying <strong>{gw(s.shortfallCoverP90)}</strong> more than the forecast suggests would have covered the
        wind shortfall in 9 out of 10 hours.
      </p>
    </section>
  )
}
