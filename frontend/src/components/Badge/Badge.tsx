import type { ReactNode } from 'react'
import styles from './Badge.module.css'

interface BadgeProps {
  variant?: 'neutral' | 'success' | 'warning' | 'danger'
  children: ReactNode
}

// Always paired with a text label (passed as children) - status is never
// conveyed by colour alone (docs/UI_GUIDELINES.md rule 9).
export function Badge({ variant = 'neutral', children }: BadgeProps) {
  return <span className={[styles.badge, styles[variant]].join(' ')}>{children}</span>
}
