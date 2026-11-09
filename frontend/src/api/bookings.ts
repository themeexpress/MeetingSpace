import { api } from './client'
import type { Booking, CreateBookingRequest } from './types'

export function createBooking(payload: CreateBookingRequest): Promise<Booking> {
  return api.post<Booking>('/bookings/', payload)
}
