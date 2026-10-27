import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { Analysis, GroupStat } from '../api'
import { gw, signedGw } from '../format'

const axis = {
  stroke: 'var(--axis)',
  tick: { fill: 'var(--muted)', fontSize: 12 },
}
const gwTick = (v: number) => `${(v / 1000).toFixed(1)}`

function Card({ title, sub, children }: { title: string; sub: string; children: React.ReactNode }) {
  return (
    <figure className="card">
      <header className="card-head">
        <div>
          <h2>{title}</h2>
          <p className="sub">{sub}</p>
        </div>
      </header>
      <div className="chart-box">{children}</div>
    </figure>
  )
}

/** Error histogram. Shortfall (wind below forecast) is red, surplus is blue. */
export function ErrorDistribution({ analysis }: { analysis: Analysis }) {
  const data = analysis.histogram.map((b) => ({
    ...b,
    mid: (b.binStart + b.binEnd) / 2,
    label: `${gwTick(b.binStart)} to ${gwTick(b.binEnd)} GW`,
  }))
  return (
    <Card
      title="How big are the misses?"
      sub="Hours by forecast error (forecast − actual, GW). Red = wind fell short, buy more."
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: 0 }} barCategoryGap={2}>
          <CartesianGrid vertical={false} stroke="var(--grid)" />
          <XAxis dataKey="mid" tickFormatter={gwTick} {...axis} />
          <YAxis allowDecimals={false} width={36} {...axis} />
          <Tooltip
            cursor={{ fill: 'var(--hover)' }}
            content={({ active, payload }) =>
              active && payload?.length ? (
                <div className="tooltip">
                  <div className="tooltip-title">{payload[0].payload.label}</div>
                  <div className="tooltip-row">
                    <b>{payload[0].payload.count}</b>&nbsp;hours
                  </div>
                </div>
              ) : null
            }
          />
          <ReferenceLine x={data.find((d) => d.binStart === 0)?.mid} stroke="var(--axis)" />
          <Bar dataKey="count" radius={[4, 4, 0, 0]} isAnimationActive={false}>
            {data.map((d) => (
              <Cell key={d.binStart} fill={d.binStart >= 0 ? 'var(--short)' : 'var(--surplus)'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Card>
  )
}

function StatTooltip({ active, payload, title }: { active?: boolean; payload?: { payload: GroupStat }[]; title: (g: GroupStat) => string }) {
  if (!active || !payload?.length) return null
  const g = payload[0].payload
  return (
    <div className="tooltip">
      <div className="tooltip-title">{title(g)}</div>
      <div className="tooltip-row">
        <i style={{ background: 'var(--series-1)' }} /> MAE <b>{gw(g.mae)}</b>
      </div>
      <div className="tooltip-row">
        <i style={{ background: 'var(--series-2)' }} /> Bias <b>{signedGw(g.bias)}</b>
      </div>
      <div className="tooltip-row muted">{g.count} forecast-hours</div>
    </div>
  )
}

/** Accuracy of every forecast run, grouped by lead time. */
export function ErrorByHorizon({ buckets, usedRange }: { buckets: GroupStat[]; usedRange: [number, number] | null }) {
  const inUse = (g: GroupStat) =>
    usedRange !== null && g.key + 4 > usedRange[0] && g.key <= usedRange[1]
  return (
    <Card
      title="Does waiting for a later forecast help?"
      sub="MAE of all forecast runs by lead time (GW). Darker bars = lead times used by your setting."
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={buckets} margin={{ top: 8, right: 8, bottom: 4, left: 0 }} barCategoryGap={2}>
          <CartesianGrid vertical={false} stroke="var(--grid)" />
          <XAxis dataKey="key" tickFormatter={(k) => `${k}h`} {...axis} />
          <YAxis tickFormatter={gwTick} width={36} {...axis} />
          <Tooltip
            cursor={{ fill: 'var(--hover)' }}
            content={<StatTooltip title={(g) => `${g.label} ahead`} />}
          />
          <Bar dataKey="mae" radius={[4, 4, 0, 0]} isAnimationActive={false}>
            {buckets.map((b) => (
              <Cell key={b.key} fill={inUse(b) ? 'var(--seq-strong)' : 'var(--seq-weak)'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Card>
  )
}

/** MAE and bias by hour of the delivery day. */
export function ErrorByHour({ analysis }: { analysis: Analysis }) {
  return (
    <Card title="Which hours are hardest?" sub="Error by hour of delivery day, UK time (GW).">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={analysis.byHour} margin={{ top: 8, right: 8, bottom: 4, left: 0 }} barCategoryGap={2}>
          <CartesianGrid vertical={false} stroke="var(--grid)" />
          <XAxis dataKey="key" tickFormatter={(h) => String(h).padStart(2, '0')} interval={2} {...axis} />
          <YAxis tickFormatter={gwTick} width={36} {...axis} />
          <Tooltip
            cursor={{ fill: 'var(--hover)' }}
            content={<StatTooltip title={(g) => `${String(g.key).padStart(2, '0')}:00 UK`} />}
          />
          <Legend wrapperStyle={{ fontSize: 13 }} />
          <ReferenceLine y={0} stroke="var(--axis)" />
          <Bar dataKey="mae" name="MAE" fill="var(--series-1)" radius={[4, 4, 0, 0]} isAnimationActive={false} />
          <Line
            dataKey="bias"
            name="Bias"
            stroke="var(--series-2)"
            strokeWidth={2}
            dot={{ r: 3 }}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </Card>
  )
}
