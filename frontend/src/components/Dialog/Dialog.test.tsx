import { useState } from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Dialog } from './Dialog'

describe('Dialog', () => {
  it('renders the title and content when open', () => {
    render(
      <Dialog open onClose={vi.fn()} title="Cancel booking">
        <p>Are you sure?</p>
      </Dialog>,
    )

    expect(screen.getByRole('dialog').hasAttribute('open')).toBe(true)
    expect(screen.getByText('Cancel booking')).toBeTruthy()
    expect(screen.getByText('Are you sure?')).toBeTruthy()
  })

  it('is not open when open=false', () => {
    render(
      <Dialog open={false} onClose={vi.fn()} title="Cancel booking">
        <p>Are you sure?</p>
      </Dialog>,
    )

    expect(screen.getByRole('dialog', { hidden: true }).hasAttribute('open')).toBe(false)
  })

  it('returns focus to the trigger element when closed', () => {
    function Harness() {
      const [open, setOpen] = useState(false)
      return (
        <>
          <button onClick={() => setOpen(true)}>Open</button>
          <Dialog open={open} onClose={() => setOpen(false)} title="Confirm">
            <button
              onClick={() => {
                const dialog = document.querySelector('dialog')
                dialog?.close()
              }}
            >
              Close
            </button>
          </Dialog>
        </>
      )
    }

    render(<Harness />)
    screen.getByText('Open').focus()
    screen.getByText('Open').click()
    screen.getByText('Close').click()

    expect(document.activeElement).toBe(screen.getByText('Open'))
  })
})
