import { useId, type SelectHTMLAttributes } from 'react'
import styles from './Select.module.css'

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string
  helpText?: string
  error?: string
}

export function Select({
  label,
  helpText,
  error,
  id,
  className,
  children,
  ...rest
}: SelectProps) {
  const generatedId = useId()
  const fieldId = id ?? generatedId
  const helpId = helpText ? `${fieldId}-help` : undefined
  const errorId = error ? `${fieldId}-error` : undefined
  const describedBy = [helpId, errorId].filter(Boolean).join(' ') || undefined

  return (
    <div className={styles.field}>
      <label className={styles.label} htmlFor={fieldId}>
        {label}
      </label>
      <select
        id={fieldId}
        className={[styles.select, error ? styles.invalid : '', className]
          .filter(Boolean)
          .join(' ')}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        {...rest}
      >
        {children}
      </select>
      {helpText && (
        <span id={helpId} className={styles.help}>
          {helpText}
        </span>
      )}
      {error && (
        <span id={errorId} className={styles.error} role="alert">
          {error}
        </span>
      )}
    </div>
  )
}
