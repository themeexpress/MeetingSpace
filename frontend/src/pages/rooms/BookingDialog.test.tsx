import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BookingDialog } from './BookingDialog'
import { ApiError } from '../../api/errors'

// Fixed far-future date so these tests never depend on the real wall clock.
const FUTURE_DATE = '2030-06-15'

const createBookingMock = vi.fn()
vi.mock('../../api/bookings', () => ({
  createBooking: (...args: unknown[]) => createBookingMock(...args),
}))

describe('BookingDialog', () => {
  beforeEach(() => {
    createBookingMock.mockReset()
  })

  it('shows the overlap message on a 409 and keeps the typed title', async () => {
    createBookingMock.mockRejectedValue(
      new ApiError(409, { detail: ['BR-6: room is already booked for part of this time range.'] }),
    )
    const user = userEvent.setup()

    render(
      <BookingDialog
        open
        onClose={vi.fn()}
        onSuccess={vi.fn()}
        roomId={1}
        roomName="Falcon"
        date={FUTURE_DATE}
        initialStartMinutes={600}
        initialEndMinutes={660}
        earliestStartMinutes={480}
        latestStartMinutes={1185}
      />,
    )

    await user.type(screen.getByLabelText('Title'), 'Sprint planning')
    await user.click(screen.getByRole('button', { name: 'Book room' }))

    expect(
      await screen.findByText('That time overlaps another booking in this room.'),
    ).toBeTruthy()
    expect(screen.getByLabelText('Title')).toHaveProperty('value', 'Sprint planning')
  })

  it('calls onSuccess with the created booking', async () => {
    const booking = {
      id: 10,
      room: { id: 1, name: 'Falcon' },
      title: 'Sprint planning',
      start_time: '2026-11-03T01:00:00+00:00',
      end_time: '2026-11-03T02:00:00+00:00',
      created_at: '2026-11-03T00:00:00+00:00',
      updated_at: '2026-11-03T00:00:00+00:00',
    }
    createBookingMock.mockResolvedValue(booking)
    const onSuccess = vi.fn()
    const user = userEvent.setup()

    render(
      <BookingDialog
        open
        onClose={vi.fn()}
        onSuccess={onSuccess}
        roomId={1}
        roomName="Falcon"
        date={FUTURE_DATE}
        initialStartMinutes={600}
        initialEndMinutes={660}
        earliestStartMinutes={480}
        latestStartMinutes={1185}
      />,
    )

    await user.type(screen.getByLabelText('Title'), 'Sprint planning')
    await user.click(screen.getByRole('button', { name: 'Book room' }))

    expect(onSuccess).toHaveBeenCalledWith(booking)
  })

  it('requires a title before submitting', async () => {
    const user = userEvent.setup()
    render(
      <BookingDialog
        open
        onClose={vi.fn()}
        onSuccess={vi.fn()}
        roomId={1}
        roomName="Falcon"
        date={FUTURE_DATE}
        initialStartMinutes={600}
        initialEndMinutes={660}
        earliestStartMinutes={480}
        latestStartMinutes={1185}
      />,
    )

    await user.click(screen.getByRole('button', { name: 'Book room' }))

    expect(screen.getByText('Enter a title for the booking.')).toBeTruthy()
    expect(createBookingMock).not.toHaveBeenCalled()
  })

  it('shows the live duration as start/end change', () => {
    render(
      <BookingDialog
        open
        onClose={vi.fn()}
        onSuccess={vi.fn()}
        roomId={1}
        roomName="Falcon"
        date={FUTURE_DATE}
        initialStartMinutes={600}
        initialEndMinutes={690}
        earliestStartMinutes={480}
        latestStartMinutes={1185}
      />,
    )

    expect(screen.getByText('1 h 30 min')).toBeTruthy()
  })
})
