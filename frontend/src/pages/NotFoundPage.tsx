import { Link } from 'react-router-dom'
import { EmptyState } from '../components/EmptyState/EmptyState'

export function NotFoundPage() {
  return (
    <div style={{ padding: '48px 16px', textAlign: 'center' }}>
      <EmptyState message="We couldn't find that page." action={<Link to="/">Go to Rooms</Link>} />
    </div>
  )
}
