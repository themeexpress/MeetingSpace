import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { Layout } from './Layout'

const useAuthMock = vi.fn()
vi.mock('../auth/useAuth', () => ({
  useAuth: () => useAuthMock(),
}))

function renderLayout() {
  render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<p>Rooms content</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

describe('Layout nav', () => {
  it('hides the Admin link for a non-staff user', () => {
    useAuthMock.mockReturnValue({
      user: { id: 1, username: 'alice', is_staff: false },
      logout: vi.fn(),
    })

    renderLayout()

    expect(screen.getByRole('link', { name: 'Rooms' })).toBeTruthy()
    expect(screen.getByRole('link', { name: 'My bookings' })).toBeTruthy()
    expect(screen.queryByRole('link', { name: 'Admin' })).toBeNull()
  })

  it('shows the Admin link for a staff user, marked as the active page', () => {
    useAuthMock.mockReturnValue({
      user: { id: 1, username: 'admin1', is_staff: true },
      logout: vi.fn(),
    })

    renderLayout()

    expect(screen.getByRole('link', { name: 'Admin' })).toBeTruthy()
    expect(screen.getByRole('link', { name: 'Rooms' }).getAttribute('aria-current')).toBe('page')
  })

  it('shows the username and a log out button', () => {
    useAuthMock.mockReturnValue({
      user: { id: 1, username: 'alice', is_staff: false },
      logout: vi.fn(),
    })

    renderLayout()

    expect(screen.getByText('alice')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Log out' })).toBeTruthy()
  })
})
