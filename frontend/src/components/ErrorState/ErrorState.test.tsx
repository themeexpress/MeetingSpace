import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ErrorState } from './ErrorState'

describe('ErrorState', () => {
  it('shows the message and calls onRetry when Retry is clicked', async () => {
    const onRetry = vi.fn()
    render(<ErrorState message="Something went wrong." onRetry={onRetry} />)

    expect(screen.getByText('Something went wrong.')).toBeTruthy()

    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })
})
