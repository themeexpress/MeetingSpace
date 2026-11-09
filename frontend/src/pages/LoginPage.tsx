import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { TextField } from '../components/TextField/TextField'
import { Button } from '../components/Button/Button'
import { ApiError, getFriendlyMessage } from '../api/errors'
import styles from './LoginPage.module.css'

interface LocationState {
  from?: { pathname: string }
}

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<{ username?: string; password?: string }>({})

  const usernameRef = useRef<HTMLInputElement>(null)
  const passwordRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    usernameRef.current?.focus()
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError(null)

    const nextFieldErrors: { username?: string; password?: string } = {}
    if (!username.trim()) nextFieldErrors.username = 'Enter your username.'
    if (!password) nextFieldErrors.password = 'Enter your password.'
    setFieldErrors(nextFieldErrors)

    if (nextFieldErrors.username) {
      usernameRef.current?.focus()
      return
    }
    if (nextFieldErrors.password) {
      passwordRef.current?.focus()
      return
    }

    setSubmitting(true)
    try {
      await login(username, password)
      const state = location.state as LocationState | null
      navigate(state?.from?.pathname ?? '/', { replace: true })
    } catch (error) {
      if (error instanceof ApiError) {
        setFormError(getFriendlyMessage(error))
      } else {
        setFormError('Something went wrong. Please try again.')
      }
      usernameRef.current?.focus()
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.card}>
        <h1 className={styles.title}>Log in</h1>
        {formError && (
          <div className={styles.banner} role="alert">
            {formError}
          </div>
        )}
        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          <TextField
            label="Username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            error={fieldErrors.username}
            inputRef={usernameRef}
            autoComplete="username"
          />
          <TextField
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            error={fieldErrors.password}
            inputRef={passwordRef}
            autoComplete="current-password"
            endAdornment={
              <button
                type="button"
                className={styles.toggle}
                onClick={() => setShowPassword((show) => !show)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            }
          />
          <Button type="submit" loading={submitting}>
            Log in
          </Button>
        </form>
      </div>
    </div>
  )
}
