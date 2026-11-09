import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { RoomsPage } from './RoomsPage'
import { ToastProvider } from '../components/Toast/ToastProvider'
import { jstWallTimeToIso } from '../lib/jst'

// Fixed far-future date so these tests never depend on the real wall clock.
const FUTURE_DATE = '2030-06-15'

const listRoomsMock = vi.fn()
const getRoomScheduleMock = vi.fn()
vi.mock('../api/rooms', () => ({
  listRooms: (...args: unknown[]) => listRoomsMock(...args),
  getRoomSchedule: (...args: unknown[]) => getRoomScheduleMock(...args),
}))

const useAuthMock = vi.fn()
vi.mock('../auth/useAuth', () => ({
  useAuth: () => useAuthMock(),
}))

const rooms = [
  { id: 1, name: 'Falcon', capacity: 8, location: '3F', is_active: true, created_at: '2026-01-01T00:00:00+00:00' },
  { id: 2, name: 'Hawk', capacity: 4, location: '2F', is_active: true, created_at: '2026-01-01T00:00:00+00:00' },
]

const falconSchedule = [
  {
    id: 100,
    title: 'Standup',
    start_time: jstWallTimeToIso(FUTURE_DATE, '10:00'),
    end_time: jstWallTimeToIso(FUTURE_DATE, '11:00'),
    booked_by: 'bob',
    is_mine: false,
  },
]

function renderPage(initialEntries: string[]) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <ToastProvider>
        <RoomsPage />
      </ToastProvider>
    </MemoryRouter>,
  )
}

describe('RoomsPage', () => {
  beforeEach(() => {
    listRoomsMock.mockReset()
    getRoomScheduleMock.mockReset()
    useAuthMock.mockReturnValue({ user: { id: 1, username: 'alice', is_staff: false } })
  })

  it('renders room cards with capacity, location, and availability', async () => {
    listRoomsMock.mockResolvedValue(rooms)
    getRoomScheduleMock.mockImplementation((roomId: number) =>
      Promise.resolve(roomId === 1 ? falconSchedule : []),
    )

    renderPage([`/?date=${FUTURE_DATE}`])

    expect((await screen.findAllByText('Falcon')).length).toBeGreaterThan(0)
    expect(screen.getByText('Hawk')).toBeTruthy()
    expect(screen.getByText('8 people')).toBeTruthy()
    expect(screen.getByText('3F')).toBeTruthy()
    expect(screen.getByText('1 booking · next free 08:00')).toBeTruthy()
    expect(screen.getByText('Free all day')).toBeTruthy()
  })

  it('narrows the visible rooms with the minimum capacity filter', async () => {
    listRoomsMock.mockResolvedValue(rooms)
    getRoomScheduleMock.mockResolvedValue([])
    const user = userEvent.setup()

    renderPage([`/?date=${FUTURE_DATE}`])
    await screen.findAllByText('Falcon')
    expect(screen.getByText('Hawk')).toBeTruthy()

    await user.selectOptions(screen.getByLabelText('Minimum capacity'), '6+')

    expect((await screen.findAllByText('Falcon')).length).toBeGreaterThan(0)
    expect(screen.queryByText('Hawk')).toBeNull()
  })

  it('clicking a free gap prefills the booking form with that start time', async () => {
    listRoomsMock.mockResolvedValue(rooms)
    getRoomScheduleMock.mockImplementation((roomId: number) =>
      Promise.resolve(roomId === 1 ? falconSchedule : []),
    )
    const user = userEvent.setup()

    renderPage([`/?room=1&date=${FUTURE_DATE}`])

    const gapButton = await screen.findByRole('button', { name: 'Free, 08:00 to 10:00. Book' })
    await user.click(gapButton)

    const startSelect = (await screen.findByLabelText('Start')) as HTMLSelectElement
    const endSelect = screen.getByLabelText('End') as HTMLSelectElement
    // 08:00 (480 min) is the gap's start; default end is +1h, capped at the
    // 10:00 (600 min) booking that follows - here +1h (540) is still inside
    // the gap, so it wins.
    expect(startSelect.value).toBe('480')
    expect(endSelect.value).toBe('540')
  })

  it('auto-selects the first room and reflects it in the URL when none is specified', async () => {
    listRoomsMock.mockResolvedValue(rooms)
    getRoomScheduleMock.mockResolvedValue([])

    renderPage([`/?date=${FUTURE_DATE}`])

    expect(
      await screen.findByRole('heading', { level: 2, name: 'Falcon' }),
    ).toBeTruthy()
    expect(screen.getByRole('button', { name: /Falcon/ }).getAttribute('aria-pressed')).toBe(
      'true',
    )
  })

  it('does not override a room explicitly chosen in the URL', async () => {
    listRoomsMock.mockResolvedValue(rooms)
    getRoomScheduleMock.mockResolvedValue([])

    renderPage([`/?room=2&date=${FUTURE_DATE}`])

    expect(await screen.findByRole('heading', { level: 2, name: 'Hawk' })).toBeTruthy()
    expect(screen.queryByRole('heading', { level: 2, name: 'Falcon' })).toBeNull()
  })

  it('shows the empty state with an admin link when there are no rooms and the user is staff', async () => {
    useAuthMock.mockReturnValue({ user: { id: 1, username: 'admin1', is_staff: true } })
    listRoomsMock.mockResolvedValue([])

    renderPage([`/?date=${FUTURE_DATE}`])

    expect(await screen.findByText('No rooms yet. An admin needs to add rooms.')).toBeTruthy()
    expect(screen.getByRole('link', { name: 'Go to Admin › Rooms' })).toBeTruthy()
  })

  it('shows the empty state without an admin link for non-staff users', async () => {
    listRoomsMock.mockResolvedValue([])

    renderPage([`/?date=${FUTURE_DATE}`])

    expect(await screen.findByText('No rooms yet. An admin needs to add rooms.')).toBeTruthy()
    expect(screen.queryByRole('link', { name: 'Go to Admin › Rooms' })).toBeNull()
  })

  it('shows an error state with Retry when rooms fail to load', async () => {
    listRoomsMock.mockRejectedValueOnce(new Error('network error'))
    listRoomsMock.mockResolvedValueOnce(rooms)
    getRoomScheduleMock.mockResolvedValue([])
    const user = userEvent.setup()

    renderPage([`/?date=${FUTURE_DATE}`])

    const retryButton = await screen.findByRole('button', { name: 'Retry' })
    await user.click(retryButton)

    expect((await screen.findAllByText('Falcon')).length).toBeGreaterThan(0)
  })
})
