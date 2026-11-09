import { useId, type InputHTMLAttributes, type ReactNode, type Ref } from 'react'
import styles from './TextField.module.css'

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  helpText?: string
  error?: string
  endAdornment?: ReactNode
  inputRef?: Ref<HTMLInputElement>
}

export function TextField({
  label,
  helpText,
  error,
  endAdornment,
  inputRef,
  id,
  className,
  ...rest
}: TextFieldProps) {
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
      <div className={styles.inputRow}>
        <input
          id={fieldId}
          ref={inputRef}
          className={[styles.input, error ? styles.invalid : '', className]
            .filter(Boolean)
            .join(' ')}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          {...rest}
        />
        {endAdornment && <span className={styles.adornment}>{endAdornment}</span>}
      </div>
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
