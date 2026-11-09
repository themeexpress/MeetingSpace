import { describe, it, expect } from 'vitest'
import {
  buildScheduleSlots,
  buildStartOptions,
  buildEndOptions,
  defaultBookingEnd,
  roundUpToStep,
  summarizeAvailability,
  GRID_START_MINUTES,
  GRID_END_MINUTES,
  MIN_DURATION_MINUTES,
  MAX_DURATION_MINUTES,
} from './scheduleUtils'

describe('buildEndOptions', () => {
  it('never offers less than 15 minutes after the start', () => {
    const options = buildEndOptions(600) // 10:00
    expect(options[0] - 600).toBe(MIN_DURATION_MINUTES)
  })

  it('never offers more than 4 hours after the start', () => {
    const options = buildEndOptions(600)
    expect(options[options.length - 1] - 600).toBe(MAX_DURATION_MINUTES)
  })

  it('every option is a 15-minute step after the start', () => {
    const options = buildEndOptions(600)
    for (const minutes of options) {
      expect((minutes - 600) % 15).toBe(0)
    }
  })
})

describe('buildStartOptions', () => {
  it('returns every 15-minute step within the range', () => {
    const options = buildStartOptions(GRID_START_MINUTES, GRID_START_MINUTES + 30)
    expect(options).toEqual([480, 495, 510])
  })

  it('returns an empty list when earliest is after latest', () => {
    expect(buildStartOptions(GRID_END_MINUTES, GRID_START_MINUTES)).toEqual([])
  })
})

describe('buildScheduleSlots', () => {
  it('fills the whole range with a single gap when there are no bookings', () => {
    const slots = buildScheduleSlots([])
    expect(slots).toEqual([
      { kind: 'gap', startMinutes: GRID_START_MINUTES, endMinutes: GRID_END_MINUTES },
    ])
  })

  it('computes gaps before, between, and after bookings', () => {
    const slots = buildScheduleSlots([
      {
        id: 1,
        title: 'Standup',
        start_time: '2026-11-03T01:00:00+00:00', // 10:00 JST
        end_time: '2026-11-03T02:00:00+00:00', // 11:00 JST
        booked_by: 'alice',
        is_mine: false,
      },
    ])

    expect(slots).toEqual([
      { kind: 'gap', startMinutes: GRID_START_MINUTES, endMinutes: 600 },
      {
        kind: 'booking',
        id: 1,
        title: 'Standup',
        startMinutes: 600,
        endMinutes: 660,
        bookedBy: 'alice',
        isMine: false,
      },
      { kind: 'gap', startMinutes: 660, endMinutes: GRID_END_MINUTES },
    ])
  })

  it('omits a gap shorter than the minimum booking duration', () => {
    const slots = buildScheduleSlots([
      {
        id: 1,
        title: 'A',
        start_time: '2026-11-02T23:05:00+00:00', // 08:05 JST (5 min after 08:00 grid start)
        end_time: '2026-11-03T01:00:00+00:00', // 10:00 JST
        booked_by: 'alice',
        is_mine: false,
      },
    ])

    expect(slots[0]).toEqual({
      kind: 'booking',
      id: 1,
      title: 'A',
      startMinutes: 485,
      endMinutes: 600,
      bookedBy: 'alice',
      isMine: false,
    })
  })

  it('does not duplicate back-to-back bookings as overlapping gaps', () => {
    const slots = buildScheduleSlots([
      {
        id: 1,
        title: 'A',
        start_time: '2026-11-03T01:00:00+00:00', // 10:00 JST
        end_time: '2026-11-03T02:00:00+00:00', // 11:00 JST
        booked_by: 'alice',
        is_mine: false,
      },
      {
        id: 2,
        title: 'B',
        start_time: '2026-11-03T02:00:00+00:00', // 11:00 JST
        end_time: '2026-11-03T03:00:00+00:00', // 12:00 JST
        booked_by: 'bob',
        is_mine: true,
      },
    ])

    const gapBetween = slots.filter(
      (slot) => slot.kind === 'gap' && slot.startMinutes === 660,
    )
    expect(gapBetween).toHaveLength(0)
  })
})

describe('defaultBookingEnd', () => {
  it('defaults to one hour after start', () => {
    expect(defaultBookingEnd(600, 900)).toBe(660)
  })

  it('caps at the gap end when the gap is shorter than one hour', () => {
    expect(defaultBookingEnd(600, 630)).toBe(630)
  })
})

describe('roundUpToStep', () => {
  it('rounds up to the next 15-minute step', () => {
    expect(roundUpToStep(601)).toBe(615)
    expect(roundUpToStep(600)).toBe(600)
  })
})

describe('summarizeAvailability', () => {
  it('reports a bookingCount of 0 and the whole day free when there are no bookings', () => {
    expect(summarizeAvailability([])).toEqual({
      bookingCount: 0,
      nextFreeMinutes: GRID_START_MINUTES,
    })
  })

  it('reports the next free gap when some of the day is booked', () => {
    const availability = summarizeAvailability([
      {
        id: 1,
        title: 'Standup',
        start_time: '2026-11-03T01:00:00+00:00', // 10:00 JST
        end_time: '2026-11-03T02:00:00+00:00', // 11:00 JST
        booked_by: 'alice',
        is_mine: false,
      },
    ])

    expect(availability).toEqual({ bookingCount: 1, nextFreeMinutes: GRID_START_MINUTES })
  })

  it('reports fully booked when there is no bookable gap left', () => {
    const availability = summarizeAvailability([
      {
        id: 1,
        title: 'All day',
        start_time: '2026-11-02T23:00:00+00:00', // 08:00 JST
        end_time: '2026-11-03T11:00:00+00:00', // 20:00 JST
        booked_by: 'alice',
        is_mine: false,
      },
    ])

    expect(availability).toEqual({ bookingCount: 1, nextFreeMinutes: null })
  })
})
