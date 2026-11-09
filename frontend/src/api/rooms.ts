import { api } from './client'
import type { Room, ScheduleEntry } from './types'

export function listRooms(): Promise<Room[]> {
  return api.get<Room[]>('/rooms/')
}

export function getRoomSchedule(roomId: number, date: string): Promise<ScheduleEntry[]> {
  return api.get<ScheduleEntry[]>(`/rooms/${roomId}/schedule/?date=${date}`)
}
