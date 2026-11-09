import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { getRoomSchedule, listRooms } from '../api/rooms'
import type { Booking, Room, ScheduleEntry } from '../api/types'
import { useAuth } from '../auth/useAuth'
import { DateControl } from '../components/DateControl/DateControl'
import { EmptyState } from '../components/EmptyState/EmptyState'
import { ErrorState } from '../components/ErrorState/ErrorState'
import { PageHeader } from '../components/PageHeader/PageHeader'
import { Select } from '../components/Select/Select'
import { Skeleton } from '../components/Skeleton/Skeleton'
import { useToast } from '../components/Toast/ToastProvider'
import {
  formatDateDisplay,
  formatTimeJst,
  isPastDateJst,
  isValidDateString,
  nowMinutesJst,
  todayInJst,
} from '../lib/jst'
import cardStyles from './rooms/RoomCard.module.css'
import { RoomCard } from './rooms/RoomCard'
import { BookingDialog } from './rooms/BookingDialog'
import { ScheduleAgenda } from './rooms/ScheduleAgenda'
import { ScheduleGrid } from './rooms/ScheduleGrid'
import {
  GRID_END_MINUTES,
  GRID_START_MINUTES,
  MIN_DURATION_MINUTES,
  buildScheduleSlots,
  defaultBookingEnd,
  roundUpToStep,
} from './rooms/scheduleUtils'
import styles from './RoomsPage.module.css'

const CAPACITY_OPTIONS = [0, 2, 4, 6, 8, 10, 20]

interface DialogState {
  startMinutes: number
  endMinutes: number
}

export function RoomsPage() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const [searchParams, setSearchParams] = useSearchParams()

  const dateParam = searchParams.get('date')
  const date = dateParam && isValidDateString(dateParam) ? dateParam : todayInJst()
  const roomParam = searchParams.get('room')
  const selectedRoomId = roomParam ? Number(roomParam) : null

  const [minCapacity, setMinCapacity] = useState(0)
  const [rooms, setRooms] = useState<Room[] | null>(null)
  const [schedules, setSchedules] = useState<Record<number, ScheduleEntry[]>>({})
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)
  const [dialogState, setDialogState] = useState<DialogState | null>(null)
  const [reloadToken, setReloadToken] = useState(0)
  const pendingFocusId = useRef<number | null>(null)

  useEffect(() => {
    let active = true
    async function load() {
      setLoading(true)
      setLoadError(false)
      try {
        const roomList = await listRooms()
        const activeRooms = roomList.filter((room) => room.is_active)
        const entries = await Promise.all(
          activeRooms.map(
            (room) => getRoomSchedule(room.id, date).then((data) => [room.id, data] as const),
          ),
        )
        if (!active) return
        setRooms(activeRooms)
        setSchedules(Object.fromEntries(entries))
      } catch {
        if (active) setLoadError(true)
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => {
      active = false
    }
  }, [date, reloadToken])

  useEffect(() => {
    if (pendingFocusId.current === null) return
    const el = document.getElementById(`booking-${pendingFocusId.current}`)
    if (el) {
      el.focus()
      pendingFocusId.current = null
    }
  }, [schedules])

  // Auto-select the first room once the list loads, if the URL didn't
  // already name one - keeps the URL as the single source of truth (a
  // refresh or shared link still lands on the same room).
  useEffect(() => {
    if (roomParam === null && rooms && rooms.length > 0) {
      const next = new URLSearchParams(searchParams)
      next.set('room', String(rooms[0].id))
      setSearchParams(next, { replace: true })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rooms, roomParam])

  function setDate(newDate: string) {
    const next = new URLSearchParams(searchParams)
    next.set('date', newDate)
    setSearchParams(next)
  }

  function selectRoom(roomId: number) {
    const next = new URLSearchParams(searchParams)
    next.set('room', String(roomId))
    setSearchParams(next)
  }

  async function refreshRoomSchedule(roomId: number) {
    const data = await getRoomSchedule(roomId, date)
    setSchedules((prev) => ({ ...prev, [roomId]: data }))
  }

  function handleSelectGap(gapStart: number, gapEnd: number) {
    setDialogState({ startMinutes: gapStart, endMinutes: defaultBookingEnd(gapStart, gapEnd) })
  }

  async function handleBookingSuccess(booking: Booking) {
    setDialogState(null)
    showToast(
      `Booked ${booking.room.name}, ${formatTimeJst(booking.start_time)}-${formatTimeJst(booking.end_time)}`,
      'success',
    )
    await refreshRoomSchedule(booking.room.id)
    pendingFocusId.current = booking.id
  }

  const visibleRooms = useMemo(
    () => (rooms ?? []).filter((room) => room.capacity >= minCapacity),
    [rooms, minCapacity],
  )
  const selectedRoom = rooms?.find((room) => room.id === selectedRoomId) ?? null
  const isToday = date === todayInJst()
  const isPast = isPastDateJst(date)

  const slots = useMemo(
    () => buildScheduleSlots(selectedRoom ? (schedules[selectedRoom.id] ?? []) : []),
    [schedules, selectedRoom],
  )

  const earliestStartMinutes = isToday
    ? Math.max(GRID_START_MINUTES, roundUpToStep(nowMinutesJst()))
    : GRID_START_MINUTES
  const latestStartMinutes = GRID_END_MINUTES - MIN_DURATION_MINUTES

  return (
    <>
      <PageHeader
        title="Rooms"
        subtitle={
          <>
            {formatDateDisplay(date)} · Times in JST
          </>
        }
      />

      <div className={styles.toolbar}>
        <Select
          label="Minimum capacity"
          value={String(minCapacity)}
          onChange={(event) => setMinCapacity(Number(event.target.value))}
        >
          {CAPACITY_OPTIONS.map((value) => (
            <option key={value} value={value}>
              {value === 0 ? 'Any' : `${value}+`}
            </option>
          ))}
        </Select>
        <DateControl date={date} onChange={setDate} />
      </div>

      {loading && (
        <div className={styles.skeletonGrid}>
          {[1, 2, 3].map((key) => (
            <div key={key} className={styles.skeletonCard}>
              <Skeleton height="24px" />
              <Skeleton width="60%" />
              <Skeleton width="40%" />
            </div>
          ))}
        </div>
      )}

      {!loading && loadError && (
        <ErrorState
          message="We couldn't load rooms. Please try again."
          onRetry={() => setReloadToken((token) => token + 1)}
        />
      )}

      {!loading && !loadError && rooms && rooms.length === 0 && (
        <EmptyState
          message="No rooms yet. An admin needs to add rooms."
          action={
            user?.is_staff ? <Link to="/admin/rooms">Go to Admin &rsaquo; Rooms</Link> : undefined
          }
        />
      )}

      {!loading && !loadError && rooms && rooms.length > 0 && visibleRooms.length === 0 && (
        <EmptyState message="No rooms match that filter." />
      )}

      {!loading && !loadError && visibleRooms.length > 0 && (
        <>
          <div className={cardStyles.grid}>
            {visibleRooms.map((room) => (
              <RoomCard
                key={room.id}
                room={room}
                entries={schedules[room.id]}
                selected={room.id === selectedRoomId}
                onSelect={() => selectRoom(room.id)}
              />
            ))}
          </div>

          {selectedRoom && (
            <section className={styles.scheduleSection} aria-label={`${selectedRoom.name} schedule`}>
              <h2 className={styles.scheduleHeading}>{selectedRoom.name}</h2>
              <ScheduleGrid
                slots={slots}
                isToday={isToday}
                onSelectGap={handleSelectGap}
                bookingDisabled={isPast}
              />
              <ScheduleAgenda slots={slots} onSelectGap={handleSelectGap} bookingDisabled={isPast} />
            </section>
          )}
        </>
      )}

      {dialogState && selectedRoom && (
        <BookingDialog
          open
          onClose={() => setDialogState(null)}
          onSuccess={handleBookingSuccess}
          roomId={selectedRoom.id}
          roomName={selectedRoom.name}
          date={date}
          initialStartMinutes={dialogState.startMinutes}
          initialEndMinutes={dialogState.endMinutes}
          earliestStartMinutes={earliestStartMinutes}
          latestStartMinutes={latestStartMinutes}
        />
      )}
    </>
  )
}
