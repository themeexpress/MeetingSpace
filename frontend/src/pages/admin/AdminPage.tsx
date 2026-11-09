import { PageHeader } from '../../components/PageHeader/PageHeader'
import { EmptyState } from '../../components/EmptyState/EmptyState'

export function AdminPage() {
  return (
    <>
      <PageHeader title="Admin" />
      <EmptyState message="Admin tools are coming soon." />
    </>
  )
}
