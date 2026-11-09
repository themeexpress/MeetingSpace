// Date/time helpers anchored to Asia/Tokyo (docs/UI_GUIDELINES.md rule 8).
// JST has no DST, so these can safely use a fixed +09:00 offset.

const TIME_ZONE = 'Asia/Tokyo'

function jstParts(iso: string) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: TIME_ZONE,
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).formatToParts(new Date(iso))
  const map: Record<string, string> = {}
  for (const part of parts) map[part.type] = part.value
  const hour = Number(map.hour) % 24
  const minute = Number(map.minute)
  return { hour, minute }
}

export function todayInJst(): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: TIME_ZONE }).format(new Date())
}

export function isValidDateString(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false
  return !Number.isNaN(new Date(`${value}T00:00:00+09:00`).getTime())
}

export function isPastDateJst(dateStr: string): boolean {
  return dateStr < todayInJst()
}

export function addDaysJst(dateStr: string, delta: number): string {
  const date = new Date(`${dateStr}T00:00:00+09:00`)
  date.setUTCDate(date.getUTCDate() + delta)
  return new Intl.DateTimeFormat('en-CA', { timeZone: TIME_ZONE }).format(date)
}

export function formatDateDisplay(dateStr: string): string {
  const date = new Date(`${dateStr}T00:00:00+09:00`)
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: TIME_ZONE,
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(date)
}

export function formatTimeJst(iso: string): string {
  const { hour, minute } = jstParts(iso)
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`
}

export function minutesFromMidnightJst(iso: string): number {
  const { hour, minute } = jstParts(iso)
  return hour * 60 + minute
}

export function nowMinutesJst(): number {
  const { hour, minute } = jstParts(new Date().toISOString())
  return hour * 60 + minute
}

export function minutesToTimeLabel(minutes: number): string {
  const hour = Math.floor(minutes / 60) % 24
  const minute = minutes % 60
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`
}

/** Convert a JST wall-clock time on a given date to a UTC ISO instant. */
export function jstWallTimeToIso(dateStr: string, hhmm: string): string {
  return new Date(`${dateStr}T${hhmm}:00+09:00`).toISOString()
}

export function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (hours === 0) return `${mins} min`
  if (mins === 0) return `${hours} h`
  return `${hours} h ${mins} min`
}
