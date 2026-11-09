import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { RequireAuth } from './RequireAuth'

const useAuthMock = vi.fn()
vi.mock('./useAuth', () => ({
  useAuth: () => useAuthMock(),
}))

describe('RequireAuth', () => {
  it('redirects to /login when there is no user', () => {
    useAuthMock.mockReturnValue({ user: null })

    render(
      <MemoryRouter initialEntries={['/my-bookings']}>
        <Routes>
          <Route
            path="/my-bookings"
            element={
              <RequireAuth>
                <p>Protected content</p>
              </RequireAuth>
            }
          />
          <Route path="/login" element={<p>Login page</p>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Login page')).toBeTruthy()
  })

  it('renders the children when there is a user', () => {
    useAuthMock.mockReturnValue({ user: { id: 1, username: 'alice', is_staff: false } })

    render(
      <MemoryRouter initialEntries={['/my-bookings']}>
        <Routes>
          <Route
            path="/my-bookings"
            element={
              <RequireAuth>
                <p>Protected content</p>
              </RequireAuth>
            }
          />
          <Route path="/login" element={<p>Login page</p>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Protected content')).toBeTruthy()
  })
})
