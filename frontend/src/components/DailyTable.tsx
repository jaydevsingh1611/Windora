import type { DayStat } from '../api'
import { gw, hourOnly, signedGw, weekdayDay } from '../format'

export function DailyTable({ days }: { days: DayStat[] }) {
  const worst = Math.max(...days.map((d) => d.mae))
  return (
    <figure className="card">
      <header className="card-head">
        <div>
          <h2>Day by day</h2>
          <p className="sub">Averages over the 24 hourly forecasts for each delivery day.</p>
        </div>
      </header>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Delivery day</th>
              <th className="num">Avg forecast</th>
              <th className="num">Avg actual</th>
              <th className="num">Bias</th>
              <th className="num">MAE</th>
              <th className="num">Worst hour</th>
            </tr>
          </thead>
          <tbody>
            {days.map((d) => (
              <tr key={d.day}>
                <td>{weekdayDay(d.day)}</td>
                <td className="num">{gw(d.meanForecast, 1)}</td>
                <td className="num">{gw(d.meanActual, 1)}</td>
                <td className={`num ${d.bias > 0 ? 'short' : 'surplus'}`}>{signedGw(d.bias, 1)}</td>
                <td className="num">
                  <span className="meter" style={{ width: `${(48 * d.mae) / worst}px` }} />
                  {gw(d.mae, 2)}
                </td>
                <td className="num">
                  {hourOnly(d.worstHour)} ({signedGw(d.worstError, 1)})
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </figure>
  )
}
