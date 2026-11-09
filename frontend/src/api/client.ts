import { ApiError, type ApiErrorMessages } from './errors'

const UNSAFE_METHODS = new Set(['POST', 'PATCH', 'PUT', 'DELETE'])

function readCookie(name: string): string {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : ''
}

function normalizeErrorBody(data: unknown): ApiErrorMessages {
  if (!data || typeof data !== 'object') return {}
  const result: ApiErrorMessages = {}
  for (const [key, value] of Object.entries(data as Record<string, unknown>)) {
    if (Array.isArray(value)) {
      result[key] = value.map(String)
    } else if (typeof value === 'string') {
      result[key] = [value]
    }
  }
  return result
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method ?? 'GET').toUpperCase()
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  if (init.body !== undefined) {
    headers.set('Content-Type', 'application/json')
  }
  if (UNSAFE_METHODS.has(method)) {
    // Read fresh every call: Django rotates the csrftoken cookie after login.
    headers.set('X-CSRFToken', readCookie('csrftoken'))
  }

  const response = await fetch(`/api${path}`, {
    ...init,
    method,
    headers,
    credentials: 'same-origin',
  })

  if (response.status === 204) {
    return undefined as T
  }

  const text = await response.text()
  let data: unknown
  try {
    data = text ? JSON.parse(text) : undefined
  } catch {
    data = undefined
  }

  if (!response.ok) {
    throw new ApiError(response.status, normalizeErrorBody(data))
  }

  return data as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
