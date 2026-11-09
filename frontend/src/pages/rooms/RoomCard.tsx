import type { Room, ScheduleEntry } from '../../api/types'
import { Badge } from '../../components/Badge/Badge'
import { Skeleton } from '../../components/Skeleton/Skeleton'
import { minutesToTimeLabel } from '../../lib/jst'
import { summarizeAvailability } from './scheduleUtils'
import styles from './RoomCard.module.css'

interface RoomCardProps {
  room: Room
  entries: ScheduleEntry[] | undefined
  selected: boolean
  onSelect: () => void
}

export function RoomCard({ room, entries, selected, onSelect }: RoomCardProps) {
  return (
    <button
      type="button"
      className={[styles.card, selected ? styles.selected : ''].filter(Boolean).join(' ')}
      aria-pressed={selected}
      onClick={onSelect}
    >
      <p className={styles.name}>{room.name}</p>
      <span className={styles.meta}>{room.capacity} people</span>
      <span className={styles.meta}>{room.location}</span>
      {entries === undefined ? (
        <Skeleton width="140px" height="1em" />
      ) : (
        <Availability entries={entries} />
      )}
      <span className={styles.affordance}>View schedule</span>
    </button>
  )
}

function Availability({ entries }: { entries: ScheduleEntry[] }) {
  const { bookingCount, nextFreeMinutes } = summarizeAvailability(entries)

  if (bookingCount === 0) {
    return <Badge variant="success">Free all day</Badge>
  }

  if (nextFreeMinutes === null) {
    return <span className={styles.availability}>Fully booked</span>
  }

  const bookingWord = bookingCount === 1 ? 'booking' : 'bookings'
  return (
    <span className={styles.availability}>
      {bookingCount} {bookingWord} · next free {minutesToTimeLabel(nextFreeMinutes)}
    </span>
  )
}
