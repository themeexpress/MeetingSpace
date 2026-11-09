import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { RoomCard } from './RoomCard'

const room = { id: 1, name: 'Falcon', capacity: 8, location: '3F', is_active: true, created_at: '2026-01-01T00:00:00+00:00' }

describe('RoomCard', () => {
  it('renders as a button with name, capacity, and location', () => {
    render(<RoomCard room={room} entries={[]} selected={false} onSelect={vi.fn()} />)

    const card = screen.getByRole('button', { name: /Falcon/ })
    expect(card.tagName).toBe('BUTTON')
    expect(screen.getByText('8 people')).toBeTruthy()
    expect(screen.getByText('3F')).toBeTruthy()
    expect(screen.getByText('View schedule')).toBeTruthy()
  })

  it('calls onSelect when clicked', async () => {
    const onSelect = vi.fn()
    const user = userEvent.setup()
    render(<RoomCard room={room} entries={[]} selected={false} onSelect={onSelect} />)

    await user.click(screen.getByRole('button', { name: /Falcon/ }))

    expect(onSelect).toHaveBeenCalledTimes(1)
  })

  it('marks the selected card with aria-pressed', () => {
    render(<RoomCard room={room} entries={[]} selected onSelect={vi.fn()} />)

    expect(screen.getByRole('button', { name: /Falcon/ }).getAttribute('aria-pressed')).toBe(
      'true',
    )
  })

  it('shows a "Free all day" badge when there are no bookings', () => {
    render(<RoomCard room={room} entries={[]} selected={false} onSelect={vi.fn()} />)

    expect(screen.getByText('Free all day')).toBeTruthy()
  })

  it('shows the booking count and next free time when partially booked', () => {
    render(
      <RoomCard
        room={room}
        entries={[
          {
            id: 1,
            title: 'Standup',
            start_time: '2026-11-03T01:00:00+00:00', // 10:00 JST
            end_time: '2026-11-03T02:00:00+00:00', // 11:00 JST
            booked_by: 'alice',
            is_mine: false,
          },
        ]}
        selected={false}
        onSelect={vi.fn()}
      />,
    )

    expect(screen.getByText('1 booking · next free 08:00')).toBeTruthy()
  })

  it('shows "Fully booked" when there is no bookable gap left', () => {
    render(
      <RoomCard
        room={room}
        entries={[
          {
            id: 1,
            title: 'All day',
            start_time: '2026-11-02T23:00:00+00:00', // 08:00 JST
            end_time: '2026-11-03T11:00:00+00:00', // 20:00 JST
            booked_by: 'alice',
            is_mine: false,
          },
        ]}
        selected={false}
        onSelect={vi.fn()}
      />,
    )

    expect(screen.getByText('Fully booked')).toBeTruthy()
  })

  it('shows a loading skeleton while entries are undefined', () => {
    const { container } = render(
      <RoomCard room={room} entries={undefined} selected={false} onSelect={vi.fn()} />,
    )

    expect(container.querySelector('[aria-hidden="true"]')).toBeTruthy()
    expect(screen.queryByText('Free all day')).toBeNull()
  })
})
