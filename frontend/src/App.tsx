import { memo, useEffect, useState } from 'react'
import { api, type Analysis, type GroupStat, type Meta, type Query, type SeriesPoint } from './api'
import { Controls } from './components/Controls'
import { DailyTable } from './components/DailyTable'
import { ErrorByHorizon, ErrorByHour, ErrorDistribution } from './components/ErrorCharts'
import { ForecastChart } from './components/ForecastChart'
import { Insight } from './components/Insight'
import { KpiTiles } from './components/KpiTiles'

interface Results {
  query: Query // the settings these results were computed for
  points: SeriesPoint[]
  analysis: Analysis
  horizon: GroupStat[]
}

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null)
  const [query, setQuery] = useState<Query | null>(null)
  const [results, setResults] = useState<Results | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .meta()
      .then((m) => {
        setMeta(m)
        setQuery({
          start: m.deliveryStart,
          end: m.deliveryEnd,
          mode: 'gate',
          gate: m.defaultGate,
          horizon: m.defaultHorizonH,
        })
      })
      .catch((e: Error) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!query) return
    let cancelled = false
    setLoading(true)
    // small debounce so dragging the lead-time slider doesn't flood the API
    const timer = setTimeout(() => {
      Promise.all([api.series(query), api.analysis(query), api.horizonAccuracy(query)])
        .then(([s, a, h]) => {
          if (cancelled) return
          setResults({ query, points: s.points, analysis: a, horizon: h.buckets })
          setError(null)
        })
        .catch((e: Error) => !cancelled && setError(e.message))
        .finally(() => !cancelled && setLoading(false))
    }, 150)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [query])

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">
          <img src="/favicon.svg" alt="" width={28} height={28} />
          <div>
            <h1>Wind Position Monitor</h1>
            <p>GB day-ahead procurement · national wind forecast vs outturn</p>
          </div>
        </div>
        {meta && (
          <div className="source">
            Source: Elexon BMRS (FUELHH, WINDFOR) · {meta.forecastRuns} forecast runs
          </div>
        )}
      </header>

      {meta && query && <Controls meta={meta} query={query} onChange={setQuery} />}

      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}

      {results && (
        <main className={loading ? 'stale' : ''} aria-busy={loading}>
          <Dashboard results={results} />
        </main>
      )}

      {!results && !error && <div className="loading">Loading forecasts…</div>}

      <footer className="foot">
        Error = forecast − actual. Positive means wind came in below forecast and the shortfall had to be bought.
        Forecasts are hourly and are scored against the actual for the matching half-hour.
      </footer>
    </div>
  )
}

// Memoised so that moving a control only re-renders the charts once new results arrive.
const Dashboard = memo(function Dashboard({ results }: { results: Results }) {
  const { analysis } = results
  return (
    <>
      <Insight analysis={analysis} query={results.query} />
      <KpiTiles analysis={analysis} />
      <ForecastChart points={results.points} summary={analysis.summary} />
      <div className="grid-3">
        <ErrorDistribution analysis={analysis} />
        <ErrorByHorizon buckets={results.horizon} usedRange={analysis.horizonRange} />
        <ErrorByHour analysis={analysis} />
      </div>
      <DailyTable days={analysis.byDay} />
    </>
  )
})
