import { PageHeader } from '../components/PageHeader/PageHeader'
import { EmptyState } from '../components/EmptyState/EmptyState'

export function MyBookingsPage() {
  return (
    <>
      <PageHeader title="My bookings" />
      <EmptyState message="Your bookings will appear here soon." />
    </>
  )
}
