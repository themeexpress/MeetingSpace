// Types mirroring docs/API.md. Keep in sync with the backend contract.

export interface User {
  id: number
  username: string
  is_staff: boolean
}

export interface Room {
  id: number
  name: string
  capacity: number
  location: string
  is_active: boolean
  created_at: string
}

export interface CreateRoomRequest {
  name: string
  capacity: number
  location: string
}

export interface UpdateRoomRequest {
  name?: string
  capacity?: number
  location?: string
  is_active?: boolean
}

export interface RoomRef {
  id: number
  name: string
}

export interface Booking {
  id: number
  room: RoomRef
  title: string
  start_time: string
  end_time: string
  created_at: string
  updated_at: string
}

export interface CreateBookingRequest {
  room: number
  title: string
  start_time: string
  end_time: string
}

export interface UpdateBookingRequest {
  title?: string
  start_time?: string
  end_time?: string
}

export interface ScheduleEntry {
  id: number
  title: string
  start_time: string
  end_time: string
  booked_by: string
  is_mine: boolean
}

export interface UserRef {
  id: number
  username: string
}

export interface AdminBooking {
  id: number
  room: RoomRef
  user: UserRef
  title: string
  start_time: string
  end_time: string
}

export interface AdminUser {
  id: number
  username: string
  is_staff: boolean
  is_active: boolean
  date_joined: string
  last_login: string | null
  upcoming_booking_count: number
  // Only present on a PATCH response that deactivated the user.
  cancelled_bookings_count?: number
}

export interface CreateUserRequest {
  username: string
  password: string
  is_staff?: boolean
}

export interface UpdateUserRequest {
  is_active?: boolean
  is_staff?: boolean
  password?: string
}
