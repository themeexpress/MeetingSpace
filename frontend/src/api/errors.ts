// ApiError + friendly copy mapping (docs/UI_GUIDELINES.md rule 7). Every
// later frontend step should surface errors through getFriendlyMessage /
// getFieldErrors rather than showing raw API text.

export type ApiErrorMessages = Record<string, string[]>

export class ApiError extends Error {
  status: number
  messages: ApiErrorMessages

  constructor(status: number, messages: ApiErrorMessages) {
    super(`API error ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.messages = messages
  }
}

// Booking-rule codes the backend embeds in its messages (see docs/SPEC.md).
const BR_CODE_MESSAGES: Record<string, string> = {
  'BR-1': 'End time must be after the start time.',
  'BR-2': "You can't book a time that's already in the past.",
  'BR-3': 'Bookings must be between 15 minutes and 4 hours long.',
  'BR-4': 'Times must be on the hour or at :15, :30 or :45.',
  'BR-5': "This room isn't available for booking right now.",
  'BR-6': 'That time overlaps another booking in this room.',
  'BR-7': 'This booking can no longer be changed.',
  'BR-8': 'Rooms and accounts are deactivated, not deleted.',
  'BR-9': "Admins can't deactivate or remove their own admin rights.",
}

const STATUS_FALLBACKS: Record<number, string> = {
  400: 'Please check the highlighted fields.',
  401: 'Please log in to continue.',
  403: "You don't have permission to do that.",
  404: "We couldn't find that.",
  405: "That action isn't available.",
  409: 'That time overlaps another booking in this room.',
  429: 'Too many attempts. Please wait a moment and try again.',
}

const GENERIC_FALLBACK = 'Something went wrong. Please try again.'

function friendlyTextFor(rawMessage: string): string | undefined {
  for (const [code, friendly] of Object.entries(BR_CODE_MESSAGES)) {
    if (rawMessage.includes(code)) return friendly
  }
  return undefined
}

function allMessages(messages: ApiErrorMessages): string[] {
  return Object.values(messages).flat()
}

/** One friendly sentence for a top-level error banner. */
export function getFriendlyMessage(error: ApiError): string {
  if (error.status === 409) return STATUS_FALLBACKS[409]

  for (const raw of allMessages(error.messages)) {
    const mapped = friendlyTextFor(raw)
    if (mapped) return mapped
  }

  const raw = allMessages(error.messages)[0]
  if (raw) return raw

  return STATUS_FALLBACKS[error.status] ?? GENERIC_FALLBACK
}

/** field name -> one friendly message, for showing errors next to fields. */
export function getFieldErrors(error: ApiError): Record<string, string> {
  const result: Record<string, string> = {}
  for (const [field, msgs] of Object.entries(error.messages)) {
    if (field === 'detail' || field === 'non_field_errors') continue
    const raw = msgs[0]
    if (raw) result[field] = friendlyTextFor(raw) ?? raw
  }
  return result
}
