const LONDON = 'Europe/London'

export const gw = (mw: number, digits = 2) => `${(mw / 1000).toFixed(digits)} GW`
export const signedGw = (mw: number, digits = 2) => `${mw >= 0 ? '+' : '−'}${gw(Math.abs(mw), digits)}`
export const mwInt = (mw: number) => `${Math.round(mw).toLocaleString('en-GB')} MW`
export const pct = (x: number, digits = 0) => `${x.toFixed(digits)}%`

export const dateTime = (iso: string) =>
  new Date(iso).toLocaleString('en-GB', {
    timeZone: LONDON,
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })

export const shortDay = (iso: string) =>
  new Date(iso).toLocaleDateString('en-GB', { timeZone: LONDON, day: '2-digit', month: 'short' })

export const weekdayDay = (isoDate: string) =>
  new Date(`${isoDate}T12:00:00Z`).toLocaleDateString('en-GB', {
    timeZone: LONDON,
    weekday: 'short',
    day: '2-digit',
    month: 'short',
  })

export const hourOnly = (iso: string) =>
  new Date(iso).toLocaleTimeString('en-GB', { timeZone: LONDON, hour: '2-digit', minute: '2-digit' })
