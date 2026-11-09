import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Select } from './Select'

describe('Select', () => {
  it('associates the visible label with the select', () => {
    render(
      <Select label="Room">
        <option value="1">Falcon</option>
      </Select>,
    )

    expect(screen.getByLabelText('Room').tagName).toBe('SELECT')
  })

  it('shows an error message and marks the field invalid', () => {
    render(
      <Select label="Room" error="Pick a room.">
        <option value="1">Falcon</option>
      </Select>,
    )

    const select = screen.getByLabelText('Room')
    expect(select.getAttribute('aria-invalid')).toBe('true')
    expect(screen.getByRole('alert').textContent).toBe('Pick a room.')
  })

  it('calls onChange when a new option is picked', async () => {
    const onChange = vi.fn()
    render(
      <Select label="Room" onChange={onChange}>
        <option value="1">Falcon</option>
        <option value="2">Hawk</option>
      </Select>,
    )

    await userEvent.selectOptions(screen.getByLabelText('Room'), '2')

    expect(onChange).toHaveBeenCalled()
  })
})
