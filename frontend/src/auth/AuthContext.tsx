import { createContext, useEffect, useState, type ReactNode } from 'react'
import { api } from '../api/client'
import type { User } from '../api/types'
import { Skeleton } from '../components/Skeleton/Skeleton'

export interface AuthContextValue {
  user: User | null
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    let active = true
    async function checkSession() {
      try {
        // Primes the csrftoken cookie too, so the login form has one ready
        // whether or not the user turns out to already be logged in.
        await api.get('/auth/csrf/')
        const me = await api.get<User>('/auth/me/')
        if (active) setUser(me)
      } catch {
        if (active) setUser(null)
      } finally {
        if (active) setChecking(false)
      }
    }
    checkSession()
    return () => {
      active = false
    }
  }, [])

  async function login(username: string, password: string) {
    const me = await api.post<User>('/auth/login/', { username, password })
    setUser(me)
  }

  async function logout() {
    await api.post('/auth/logout/')
    setUser(null)
  }

  if (checking) {
    return (
      <div style={{ padding: '24px', maxWidth: '480px', margin: '0 auto' }}>
        <Skeleton height="32px" />
        <div style={{ height: '16px' }} />
        <Skeleton height="200px" />
      </div>
    )
  }

  return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>
}
