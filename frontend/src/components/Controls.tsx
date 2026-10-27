import type { Meta, Query } from '../api'

interface Props {
  meta: Meta
  query: Query
  onChange: (q: Query) => void
}

export function Controls({ meta, query, onChange }: Props) {
  const set = (patch: Partial<Query>) => onChange({ ...query, ...patch })

  return (
    <section className="controls" aria-label="Analysis settings">
      <label className="field">
        <span>Delivery from</span>
        <input
          type="date"
          value={query.start}
          min={meta.deliveryStart}
          max={query.end}
          onChange={(e) => e.target.value && set({ start: e.target.value })}
        />
      </label>
      <label className="field">
        <span>Delivery to</span>
        <input
          type="date"
          value={query.end}
          min={query.start}
          max={meta.deliveryEnd}
          onChange={(e) => e.target.value && set({ end: e.target.value })}
        />
      </label>

      <div className="field">
        <span>Forecast used</span>
        <div className="segmented" role="radiogroup" aria-label="Forecast selection rule">
          <button
            role="radio"
            aria-checked={query.mode === 'gate'}
            className={query.mode === 'gate' ? 'on' : ''}
            onClick={() => set({ mode: 'gate' })}
          >
            At decision gate
          </button>
          <button
            role="radio"
            aria-checked={query.mode === 'horizon'}
            className={query.mode === 'horizon' ? 'on' : ''}
            onClick={() => set({ mode: 'horizon' })}
          >
            Fixed lead time
          </button>
        </div>
      </div>

      {query.mode === 'gate' ? (
        <label className="field">
          <span>Gate closure on D-1 (UK)</span>
          <input
            type="time"
            step={600}
            value={query.gate}
            onChange={(e) => e.target.value && set({ gate: e.target.value })}
          />
        </label>
      ) : (
        <label className="field grow">
          <span>
            Minimum lead time: <strong>{query.horizon}h</strong>
          </span>
          <input
            type="range"
            min={0}
            max={meta.maxHorizonH}
            step={1}
            value={query.horizon}
            onChange={(e) => set({ horizon: Number(e.target.value) })}
          />
        </label>
      )}

      <div className="presets">
        <button
          className="ghost"
          onClick={() => set({ start: meta.deliveryStart, end: meta.deliveryEnd })}
        >
          Full pilot
        </button>
        <button className="ghost" onClick={() => set({ start: '2026-01-12', end: '2026-01-18' })}>
          Sample week
        </button>
      </div>
    </section>
  )
}
