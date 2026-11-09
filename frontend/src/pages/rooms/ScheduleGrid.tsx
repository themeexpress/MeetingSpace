import { useEffect, useState } from 'react'
import { Badge } from '../../components/Badge/Badge'
import { minutesToTimeLabel, nowMinutesJst } from '../../lib/jst'
import {
  GRID_END_MINUTES,
  GRID_START_MINUTES,
  type ScheduleSlot,
} from './scheduleUtils'
import styles from './ScheduleGrid.module.css'

const HOUR_PX = 60

// Always ticks; the caller decides whether "now" is relevant to display
// (e.g. only on today's grid). Keeps the effect a pure subscription, with
// setState only inside the interval callback.
function useNowMinutesJst(): number {
  const [now, setNow] = useState<number>(() => nowMinutesJst())

  useEffect(() => {
    const interval = setInterval(() => setNow(nowMinutesJst()), 60_000)
    return () => clearInterval(interval)
  }, [])

  return now
}

interface ScheduleGridProps {
  slots: ScheduleSlot[]
  isToday: boolean
  onSelectGap: (startMinutes: number, endMinutes: number) => void
  bookingDisabled: boolean
}

export function ScheduleGrid({
  slots,
  isToday,
  onSelectGap,
  bookingDisabled,
}: ScheduleGridProps) {
  const nowMinutes = useNowMinutesJst()
  const totalMinutes = GRID_END_MINUTES - GRID_START_MINUTES
  const heightPx = (totalMinutes / 60) * HOUR_PX

  const hourMarks: number[] = []
  for (let m = GRID_START_MINUTES; m <= GRID_END_MINUTES; m += 60) hourMarks.push(m)

  const quarterMarks: number[] = []
  for (let m = GRID_START_MINUTES; m <= GRID_END_MINUTES; m += 15) {
    if (m % 60 !== 0) quarterMarks.push(m)
  }

  function topFor(minutes: number) {
    return ((minutes - GRID_START_MINUTES) / 60) * HOUR_PX
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.hourLabels} style={{ height: heightPx }}>
        {hourMarks.map((minutes) => (
          <span key={minutes} className={styles.hourLabel} style={{ top: topFor(minutes) }}>
            {minutesToTimeLabel(minutes)}
          </span>
        ))}
      </div>
      <div className={styles.track} style={{ height: heightPx }}>
        {hourMarks.map((minutes) => (
          <div key={minutes} className={styles.hourLine} style={{ top: topFor(minutes) }} />
        ))}
        {quarterMarks.map((minutes) => (
          <div key={minutes} className={styles.quarterLine} style={{ top: topFor(minutes) }} />
        ))}

        {slots.map((slot) => {
          const top = topFor(slot.startMinutes)
          const height = topFor(slot.endMinutes) - top

          if (slot.kind === 'booking') {
            const range = `${minutesToTimeLabel(slot.startMinutes)} to ${minutesToTimeLabel(slot.endMinutes)}`
            const name = `${slot.title}, ${range}, booked by ${slot.bookedBy}${
              slot.isMine ? ', Your booking' : ''
            }`
            return (
              <button
                key={slot.id}
                id={`booking-${slot.id}`}
                type="button"
                className={`${styles.block} ${styles.bookingBlock}`}
                style={{ top, height }}
                aria-label={name}
              >
                <strong>{slot.title}</strong>
                <div>{range}</div>
                <div>{slot.bookedBy}</div>
                {slot.isMine && <Badge variant="success">Your booking</Badge>}
              </button>
            )
          }

          const range = `${minutesToTimeLabel(slot.startMinutes)} to ${minutesToTimeLabel(slot.endMinutes)}`
          if (bookingDisabled) {
            return (
              <div
                key={`gap-${slot.startMinutes}`}
                className={`${styles.block} ${styles.gapTextOnly}`}
                style={{ top, height }}
              >
                Free, {range}
              </div>
            )
          }
          return (
            <button
              key={`gap-${slot.startMinutes}`}
              type="button"
              className={`${styles.block} ${styles.gapBlock}`}
              style={{ top, height }}
              aria-label={`Free, ${range}. Book`}
              onClick={() => onSelectGap(slot.startMinutes, slot.endMinutes)}
            >
              Free, {range}
            </button>
          )
        })}

        {isToday &&
          nowMinutes >= GRID_START_MINUTES &&
          nowMinutes <= GRID_END_MINUTES && (
            <div className={styles.nowLine} style={{ top: topFor(nowMinutes) }}>
              <span className={styles.nowLabel}>Now</span>
            </div>
          )}
      </div>
    </div>
  )
}
