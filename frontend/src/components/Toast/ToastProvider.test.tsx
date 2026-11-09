import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ToastProvider, useToast } from './ToastProvider'

function ShowToastButton({ message = 'Booking cancelled' }: { message?: string }) {
  const { showToast } = useToast()
  return <button onClick={() => showToast(message, 'success')}>Trigger</button>
}

describe('ToastProvider / useToast', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows a toast announced via role=status', async () => {
    const user = userEvent.setup()
    render(
      <ToastProvider>
        <ShowToastButton />
      </ToastProvider>,
    )

    await user.click(screen.getByRole('button', { name: 'Trigger' }))

    expect(screen.getByRole('status').textContent).toContain('Booking cancelled')
  })

  it('dismisses a toast when its close button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <ToastProvider>
        <ShowToastButton />
      </ToastProvider>,
    )

    await user.click(screen.getByRole('button', { name: 'Trigger' }))
    expect(screen.getByRole('status').textContent).toContain('Booking cancelled')

    await user.click(screen.getByRole('button', { name: 'Dismiss notification' }))

    expect(screen.getByRole('status').textContent).not.toContain('Booking cancelled')
  })

  it('throws when used outside a ToastProvider', () => {
    function Bare() {
      useToast()
      return null
    }
    expect(() => render(<Bare />)).toThrow('useToast must be used within a ToastProvider')
  })
})
