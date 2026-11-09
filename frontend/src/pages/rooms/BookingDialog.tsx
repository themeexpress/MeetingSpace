import { useEffect, useRef, useState, type FormEvent } from 'react'
import { createBooking } from '../../api/bookings'
import { ApiError, getFieldErrors, getFriendlyMessage } from '../../api/errors'
import type { Booking } from '../../api/types'
import { Button } from '../../components/Button/Button'
import { Dialog } from '../../components/Dialog/Dialog'
import dialogStyles from '../../components/Dialog/Dialog.module.css'
import { Select } from '../../components/Select/Select'
import { TextField } from '../../components/TextField/TextField'
import { formatDuration, jstWallTimeToIso, minutesToTimeLabel, nowMinutesJst, todayInJst } from '../../lib/jst'
import { buildEndOptions, buildStartOptions } from './scheduleUtils'
import styles from './BookingDialog.module.css'

const TITLE_MAX_LENGTH = 120

interface BookingDialogProps {
  open: boolean
  onClose: () => void
  roomId: number
  roomName: string
  date: string
  initialStartMinutes: number
  initialEndMinutes: number
  earliestStartMinutes: number
  latestStartMinutes: number
  onSuccess: (booking: Booking) => void
}

export function BookingDialog({
  open,
  onClose,
  roomId,
  roomName,
  date,
  initialStartMinutes,
  initialEndMinutes,
  earliestStartMinutes,
  latestStartMinutes,
  onSuccess,
}: BookingDialogProps) {
  const [title, setTitle] = useState('')
  const [startMinutes, setStartMinutes] = useState(initialStartMinutes)
  const [endMinutes, setEndMinutes] = useState(initialEndMinutes)
  const [submitting, setSubmitting] = useState(false)
  const [bannerError, setBannerError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const titleRef = useRef<HTMLInputElement>(null)

  // BookingDialog is only ever mounted while a gap is selected (RoomsPage
  // renders it conditionally), so every open is already a fresh mount with
  // correct initial state - no reset-on-prop-change effect needed, and a
  // failed submit naturally keeps the user's input since nothing remounts.
  useEffect(() => {
    titleRef.current?.focus()
  }, [])

  const startOptions = buildStartOptions(earliestStartMinutes, latestStartMinutes)
  const endOptions = buildEndOptions(startMinutes)

  function handleStartChange(newStart: number) {
    const duration = endMinutes - startMinutes
    const options = buildEndOptions(newStart)
    const desired = newStart + duration
    setStartMinutes(newStart)
    setEndMinutes(options.includes(desired) ? desired : options[0])
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBannerError(null)
    setFieldErrors({})

    const trimmedTitle = title.trim()
    const errors: Record<string, string> = {}
    if (!trimmedTitle) {
      errors.title = 'Enter a title for the booking.'
    } else if (trimmedTitle.length > TITLE_MAX_LENGTH) {
      errors.title = `Keep the title under ${TITLE_MAX_LENGTH} characters.`
    }
    if (date === todayInJst() && startMinutes < nowMinutesJst()) {
      errors.start_time = "You can't book a time that's already in the past."
    }

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors)
      titleRef.current?.focus()
      return
    }

    setSubmitting(true)
    try {
      const booking = await createBooking({
        room: roomId,
        title: trimmedTitle,
        start_time: jstWallTimeToIso(date, minutesToTimeLabel(startMinutes)),
        end_time: jstWallTimeToIso(date, minutesToTimeLabel(endMinutes)),
      })
      onSuccess(booking)
    } catch (error) {
      if (error instanceof ApiError) {
        setBannerError(getFriendlyMessage(error))
        setFieldErrors(getFieldErrors(error))
      } else {
        setBannerError('Something went wrong. Please try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} title="Book a room">
      <form className={styles.form} onSubmit={handleSubmit} noValidate>
        {bannerError && (
          <div className={styles.banner} role="alert">
            {bannerError}
          </div>
        )}

        <div className={styles.readOnlyField}>
          <span className={styles.readOnlyLabel}>Room</span>
          <span className={styles.readOnlyValue}>{roomName}</span>
        </div>

        <TextField
          label="Title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          maxLength={TITLE_MAX_LENGTH}
          error={fieldErrors.title}
          inputRef={titleRef}
        />

        <div className={styles.timeRow}>
          <Select
            label="Start"
            value={String(startMinutes)}
            onChange={(event) => handleStartChange(Number(event.target.value))}
            error={fieldErrors.start_time}
          >
            {startOptions.map((minutes) => (
              <option key={minutes} value={minutes}>
                {minutesToTimeLabel(minutes)}
              </option>
            ))}
          </Select>
          <Select
            label="End"
            value={String(endMinutes)}
            onChange={(event) => setEndMinutes(Number(event.target.value))}
            error={fieldErrors.end_time}
          >
            {endOptions.map((minutes) => (
              <option key={minutes} value={minutes}>
                {minutesToTimeLabel(minutes)}
              </option>
            ))}
          </Select>
        </div>

        <p className={styles.duration}>{formatDuration(endMinutes - startMinutes)}</p>
        <p className={styles.jstNote}>Times in JST</p>

        <div className={dialogStyles.actions}>
          <Button type="button" variant="secondary" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button type="submit" loading={submitting}>
            Book room
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
