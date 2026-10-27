export type Mode = 'gate' | 'horizon'

export interface Query {
  start: string
  end: string
  mode: Mode
  gate: string
  horizon: number
}

export interface Meta {
  deliveryStart: string
  deliveryEnd: string
  defaultGate: string
  defaultHorizonH: number
  maxHorizonH: number
  forecastRuns: number
  dataSource: string
  fetchedAt: string
}

export interface SeriesPoint {
  time: string
  actual: number | null
  forecast: number | null
  publishTime: string | null
  horizonH: number | null
}

export interface Summary {
  count: number
  mae: number
  rmse: number
  bias: number
  maePctOfMeanActual: number
  meanActual: number
  p10: number
  p50: number
  p90: number
  p95AbsError: number
  maxAbsError: number
  shortfallCoverP90: number
  shareOverForecast: number
}

export interface GroupStat {
  key: number
  label?: string
  count: number
  mae: number
  bias: number
  p10: number
  p90: number
}

export interface DayStat {
  day: string
  count: number
  meanForecast: number
  meanActual: number
  mae: number
  bias: number
  worstHour: string
  worstError: number
}

export interface Analysis {
  summary: Summary
  horizonRange: [number, number] | null
  runsUsed: number
  byHour: GroupStat[]
  byDay: DayStat[]
  histogram: { binStart: number; binEnd: number; count: number }[]
}

const BASE = import.meta.env.VITE_API_BASE ?? ''

async function get<T>(path: string, q?: Query): Promise<T> {
  const params = q
    ? '?' + new URLSearchParams({ ...q, horizon: String(q.horizon) }).toString()
    : ''
  const res = await fetch(`${BASE}/api/${path}${params}`)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(typeof body.detail === 'string' ? body.detail : `Request failed (${res.status})`)
  }
  return res.json() as Promise<T>
}

export const api = {
  meta: () => get<Meta>('meta'),
  series: (q: Query) => get<{ points: SeriesPoint[] }>('series', q),
  analysis: (q: Query) => get<Analysis>('analysis', q),
  horizonAccuracy: (q: Query) => get<{ buckets: GroupStat[] }>('horizon-accuracy', q),
}
