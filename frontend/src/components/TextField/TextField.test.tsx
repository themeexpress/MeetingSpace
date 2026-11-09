import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TextField } from './TextField'

describe('TextField', () => {
  it('associates the visible label with the input', () => {
    render(<TextField label="Username" />)

    const input = screen.getByLabelText('Username')
    expect(input.tagName).toBe('INPUT')
  })

  it('shows help text and links it via aria-describedby', () => {
    render(<TextField label="Username" helpText="Letters and numbers only" />)

    const input = screen.getByLabelText('Username')
    const describedBy = input.getAttribute('aria-describedby')
    expect(describedBy).toBeTruthy()
    expect(screen.getByText('Letters and numbers only').id).toBe(describedBy)
  })

  it('shows an error message and marks the field invalid', () => {
    render(<TextField label="Username" error="This field is required." />)

    const input = screen.getByLabelText('Username')
    expect(input.getAttribute('aria-invalid')).toBe('true')
    expect(screen.getByRole('alert').textContent).toBe('This field is required.')
  })

  it('keeps the user input value after an error', () => {
    render(<TextField label="Username" error="Oops" defaultValue="alice" />)

    expect(screen.getByLabelText('Username')).toHaveProperty('value', 'alice')
  })

  it('passes through input events', async () => {
    const onChange = vi.fn()
    render(<TextField label="Username" onChange={onChange} />)

    await userEvent.type(screen.getByLabelText('Username'), 'a')

    expect(onChange).toHaveBeenCalled()
  })
})
