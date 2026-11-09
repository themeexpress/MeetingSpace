import type { ScheduleEntry } from '../../api/types'
import { minutesFromMidnightJst } from '../../lib/jst'

export const GRID_START_MINUTES = 8 * 60 // 08:00
export const GRID_END_MINUTES = 20 * 60 // 20:00
export const STEP_MINUTES = 15
export const MIN_DURATION_MINUTES = 15
export const MAX_DURATION_MINUTES = 4 * 60

export type ScheduleSlot =
  | {
      kind: 'booking'
      id: number
      title: string
      startMinutes: number
      endMinutes: number
      bookedBy: string
      isMine: boolean
    }
  | { kind: 'gap'; startMinutes: number; endMinutes: number }

/** Merge a room's bookings with the free gaps between them, within [rangeStart, rangeEnd). */
export function buildScheduleSlots(
  entries: ScheduleEntry[],
  rangeStart: number = GRID_START_MINUTES,
  rangeEnd: number = GRID_END_MINUTES,
): ScheduleSlot[] {
  const bookings = entries
    .map((entry) => ({
      kind: 'booking' as const,
      id: entry.id,
      title: entry.title,
      startMinutes: minutesFromMidnightJst(entry.start_time),
      endMinutes: minutesFromMidnightJst(entry.end_time),
      bookedBy: entry.booked_by,
      isMine: entry.is_mine,
    }))
    .sort((a, b) => a.startMinutes - b.startMinutes)

  const slots: ScheduleSlot[] = []
  let cursor = rangeStart

  for (const booking of bookings) {
    const start = Math.max(booking.startMinutes, rangeStart)
    const end = Math.min(booking.endMinutes, rangeEnd)
    if (start - cursor >= MIN_DURATION_MINUTES) {
      slots.push({ kind: 'gap', startMinutes: cursor, endMinutes: start })
    }
    slots.push(booking)
    cursor = Math.max(cursor, end)
  }

  if (rangeEnd - cursor >= MIN_DURATION_MINUTES) {
    slots.push({ kind: 'gap', startMinutes: cursor, endMinutes: rangeEnd })
  }

  return slots
}

export function roundUpToStep(minutes: number, step: number = STEP_MINUTES): number {
  return Math.ceil(minutes / step) * step
}

function buildTimeOptions(start: number, end: number, step: number = STEP_MINUTES): number[] {
  const options: number[] = []
  for (let m = start; m <= end; m += step) options.push(m)
  return options
}

/** Start-time options, 15-minute steps, from earliestMinutes up to the last
 * minute a MIN_DURATION_MINUTES booking could still start. */
export function buildStartOptions(earliestMinutes: number, latestMinutes: number): number[] {
  if (earliestMinutes > latestMinutes) return []
  return buildTimeOptions(earliestMinutes, latestMinutes, STEP_MINUTES)
}

/** End-time options for a given start: BR-3 enforced by construction
 * (never < MIN_DURATION_MINUTES or > MAX_DURATION_MINUTES after start). */
export function buildEndOptions(startMinutes: number): number[] {
  return buildTimeOptions(
    startMinutes + MIN_DURATION_MINUTES,
    startMinutes + MAX_DURATION_MINUTES,
    STEP_MINUTES,
  )
}

/** Default end when opening the dialog from a free gap: +1 hour, or the gap's end if sooner. */
export function defaultBookingEnd(startMinutes: number, gapEndMinutes: number): number {
  return Math.min(startMinutes + 60, gapEndMinutes)
}

export interface RoomAvailability {
  bookingCount: number
  /** Start of the earliest bookable (>=15 min) gap in the day, or null if there is none. */
  nextFreeMinutes: number | null
}

/** Summarise a room's day for the room card: how many bookings, and when the
 * next bookable gap starts (null means every bookable slot is taken). */
export function summarizeAvailability(entries: ScheduleEntry[]): RoomAvailability {
  const firstGap = buildScheduleSlots(entries).find((slot) => slot.kind === 'gap')
  return {
    bookingCount: entries.length,
    nextFreeMinutes: firstGap ? firstGap.startMinutes : null,
  }
}
