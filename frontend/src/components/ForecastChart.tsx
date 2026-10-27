import { useMemo, useState } from 'react'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { SeriesPoint, Summary } from '../api'
import { dateTime, gw, hourOnly, shortDay } from '../format'

interface Props {
  points: SeriesPoint[]
  summary: Summary
}

interface Row {
  t: number
  actual: number | null
  forecast: number | null
  band: [number, number] | null
  publishTime: string | null
  horizonH: number | null
  // forecast for the hour this half-hour belongs to (forecasts are hourly), used by the tooltip
  hourly: SeriesPoint | null
}

const HALF_HOUR_MS = 30 * 60 * 1000

export function ForecastChart({ points, summary }: Props) {
  const [showBand, setShowBand] = useState(true)

  const rows: Row[] = useMemo(() => {
    let lastForecast: SeriesPoint | null = null
    return points.map((p) => {
      const t = Date.parse(p.time)
      if (p.forecast !== null) lastForecast = p
      return {
        t,
        actual: p.actual,
        forecast: p.forecast,
        // actual = forecast - error, so the P10..P90 error range maps to [forecast - p90, forecast - p10]
        band:
          p.forecast === null ? null : [Math.max(0, p.forecast - summary.p90), p.forecast - summary.p10],
        publishTime: p.publishTime,
        horizonH: p.horizonH,
        hourly: lastForecast && t - Date.parse(lastForecast.time) <= HALF_HOUR_MS ? lastForecast : null,
      }
    })
  }, [points, summary.p10, summary.p90])

  const days = new Set(points.map((p) => shortDay(p.time))).size
  const ticks = useMemo(() => {
    // one tick per day (or every few days for long ranges), at UK midnight
    const step = days > 14 ? 4 : days > 7 ? 2 : 1
    const seen: number[] = []
    for (const r of rows) {
      const d = new Date(r.t)
      if (d.getUTCHours() === 0 && d.getUTCMinutes() === 0) seen.push(r.t)
    }
    return seen.filter((_, i) => i % step === 0)
  }, [rows, days])

  return (
    <figure className="card chart-card">
      <header className="card-head">
        <div>
          <h2>Wind generation: actual vs forecast used for buying</h2>
          <p className="sub">National wind output, MW. Actuals every 30 min, forecasts hourly.</p>
        </div>
        <label className="toggle">
          <input type="checkbox" checked={showBand} onChange={(e) => setShowBand(e.target.checked)} />
          P10–P90 range for actual output
        </label>
      </header>
      <div className="chart-box tall">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={rows} margin={{ top: 8, right: 16, bottom: 4, left: 8 }}>
            <CartesianGrid vertical={false} stroke="var(--grid)" />
            <XAxis
              dataKey="t"
              type="number"
              scale="time"
              domain={['dataMin', 'dataMax']}
              ticks={ticks}
              tickFormatter={(t) => shortDay(new Date(t).toISOString())}
              stroke="var(--axis)"
              tick={{ fill: 'var(--muted)', fontSize: 12 }}
            />
            <YAxis
              tickFormatter={(v) => `${(v / 1000).toFixed(0)} GW`}
              stroke="var(--axis)"
              tick={{ fill: 'var(--muted)', fontSize: 12 }}
              width={56}
            />
            <Tooltip content={<SeriesTooltip />} />
            <Legend wrapperStyle={{ fontSize: 13, color: 'var(--text-2)' }} />
            {showBand && (
              <Area
                dataKey="band"
                name="Likely actual range (P10–P90)"
                stroke="none"
                fill="var(--series-2)"
                fillOpacity={0.15}
                connectNulls
                isAnimationActive={false}
                legendType="square"
              />
            )}
            <Line
              dataKey="actual"
              name="Actual (FUELHH)"
              stroke="var(--series-1)"
              strokeWidth={2}
              dot={false}
              connectNulls
              isAnimationActive={false}
            />
            <Line
              dataKey="forecast"
              name="Forecast at decision time (WINDFOR)"
              stroke="var(--series-2)"
              strokeWidth={2}
              dot={false}
              connectNulls
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="sub">
        Shaded band: the range the actual output fell within 80% of the time, given the forecast and this
        period's error distribution ({gw(summary.p10, 1)} to {gw(summary.p90, 1)} error).
      </figcaption>
    </figure>
  )
}

interface TooltipProps {
  active?: boolean
  payload?: { payload: Row }[]
}

function SeriesTooltip({ active, payload }: TooltipProps) {
  if (!active || !payload?.length) return null
  const r = payload[0].payload
  const f = r.hourly
  return (
    <div className="tooltip">
      <div className="tooltip-title">{dateTime(new Date(r.t).toISOString())}</div>
      {r.actual !== null && (
        <div className="tooltip-row">
          <i style={{ background: 'var(--series-1)' }} /> Actual <b>{gw(r.actual)}</b>
        </div>
      )}
      {f && (
        <>
          <div className="tooltip-row">
            <i style={{ background: 'var(--series-2)' }} />
            {f === r.hourly && r.forecast === null ? `Forecast (${hourOnly(f.time)} hour)` : 'Forecast'}
            <b>{gw(f.forecast!)}</b>
          </div>
          {r.actual !== null && (
            <div className="tooltip-row muted">
              Error <b>{gw(f.forecast! - r.actual)}</b>
            </div>
          )}
          <div className="tooltip-row muted">
            Run published {dateTime(f.publishTime!)} ({f.horizonH}h ahead)
          </div>
        </>
      )}
    </div>
  )
}
