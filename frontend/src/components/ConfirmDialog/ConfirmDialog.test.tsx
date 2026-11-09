import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ConfirmDialog } from './ConfirmDialog'

describe('ConfirmDialog', () => {
  it('names the item and explains the effect', () => {
    render(
      <ConfirmDialog
        open
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        title="Cancel booking"
        message='Cancel "Sprint planning"? This cannot be undone.'
      />,
    )

    expect(screen.getByText('Cancel "Sprint planning"? This cannot be undone.')).toBeTruthy()
  })

  it('calls onConfirm when the confirm button is clicked', async () => {
    const onConfirm = vi.fn()
    render(
      <ConfirmDialog
        open
        onClose={vi.fn()}
        onConfirm={onConfirm}
        title="Cancel booking"
        message="Are you sure?"
        confirmLabel="Cancel booking"
      />,
    )

    await userEvent.click(screen.getByRole('button', { name: 'Cancel booking' }))

    expect(onConfirm).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when the cancel button is clicked', async () => {
    const onClose = vi.fn()
    render(
      <ConfirmDialog
        open
        onClose={onClose}
        onConfirm={vi.fn()}
        title="Cancel booking"
        message="Are you sure?"
      />,
    )

    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(onClose).toHaveBeenCalledTimes(1)
  })
})
