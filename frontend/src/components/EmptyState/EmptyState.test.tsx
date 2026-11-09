import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { EmptyState } from './EmptyState'
import { Button } from '../Button/Button'

describe('EmptyState', () => {
  it('shows the message and the next action', async () => {
    const onClick = vi.fn()
    render(
      <EmptyState
        message="No rooms yet."
        action={<Button onClick={onClick}>Add a room</Button>}
      />,
    )

    expect(screen.getByText('No rooms yet.')).toBeTruthy()

    await userEvent.click(screen.getByRole('button', { name: 'Add a room' }))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('renders without an action', () => {
    render(<EmptyState message="No bookings yet." />)

    expect(screen.getByText('No bookings yet.')).toBeTruthy()
  })
})
