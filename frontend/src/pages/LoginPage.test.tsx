import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { LoginPage } from './LoginPage'
import { ApiError } from '../api/errors'

const loginMock = vi.fn()

vi.mock('../auth/useAuth', () => ({
  useAuth: () => ({ login: loginMock }),
}))

describe('LoginPage', () => {
  beforeEach(() => {
    loginMock.mockReset()
  })

  it('focuses the username field on load', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    expect(document.activeElement).toBe(screen.getByLabelText('Username'))
  })

  it('shows the API error above the form on a 400', async () => {
    loginMock.mockRejectedValue(
      new ApiError(400, { non_field_errors: ['Unable to log in with provided credentials.'] }),
    )
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText('Username'), 'alice')
    await user.type(screen.getByLabelText('Password'), 'wrong-password')
    await user.click(screen.getByRole('button', { name: 'Log in' }))

    expect(screen.getByRole('alert').textContent).toBe(
      'Unable to log in with provided credentials.',
    )
  })

  it('disables the submit button while the request is in flight', async () => {
    let resolveLogin: () => void = () => {}
    loginMock.mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          resolveLogin = resolve
        }),
    )
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText('Username'), 'alice')
    await user.type(screen.getByLabelText('Password'), 'correct-password')
    await user.click(screen.getByRole('button', { name: 'Log in' }))

    expect(screen.getByRole('button', { name: 'Log in' }).hasAttribute('disabled')).toBe(true)
    resolveLogin()
  })

  it('shows field errors and focuses the first invalid field when submitted empty', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    await user.click(screen.getByRole('button', { name: 'Log in' }))

    expect(screen.getByText('Enter your username.')).toBeTruthy()
    expect(document.activeElement).toBe(screen.getByLabelText('Username'))
    expect(loginMock).not.toHaveBeenCalled()
  })
})
