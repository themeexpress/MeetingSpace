import { Badge } from '../../components/Badge/Badge'
import { minutesToTimeLabel } from '../../lib/jst'
import type { ScheduleSlot } from './scheduleUtils'
import styles from './ScheduleAgenda.module.css'

interface ScheduleAgendaProps {
  slots: ScheduleSlot[]
  onSelectGap: (startMinutes: number, endMinutes: number) => void
  bookingDisabled: boolean
}

export function ScheduleAgenda({ slots, onSelectGap, bookingDisabled }: ScheduleAgendaProps) {
  return (
    <ul className={styles.list}>
      {slots.map((slot) => {
        const start = minutesToTimeLabel(slot.startMinutes)
        const end = minutesToTimeLabel(slot.endMinutes)

        if (slot.kind === 'booking') {
          const name = `${slot.title}, ${start} to ${end}, booked by ${slot.bookedBy}${
            slot.isMine ? ', Your booking' : ''
          }`
          return (
            <li key={slot.id}>
              <button
                id={`booking-${slot.id}`}
                type="button"
                className={`${styles.item} ${styles.booking}`}
                aria-label={name}
              >
                <strong>{slot.title}</strong>
                <span>
                  {start}-{end} · {slot.bookedBy}
                </span>
                {slot.isMine && <Badge variant="success">Your booking</Badge>}
              </button>
            </li>
          )
        }

        if (bookingDisabled) {
          return (
            <li key={`gap-${slot.startMinutes}`}>
              <div className={`${styles.item} ${styles.gapTextOnly}`}>
                Free {start}-{end}
              </div>
            </li>
          )
        }

        return (
          <li key={`gap-${slot.startMinutes}`}>
            <button
              type="button"
              className={`${styles.item} ${styles.gap}`}
              aria-label={`Free, ${start} to ${end}. Book`}
              onClick={() => onSelectGap(slot.startMinutes, slot.endMinutes)}
            >
              Free {start}-{end} · Book
            </button>
          </li>
        )
      })}
    </ul>
  )
}
