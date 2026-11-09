import { Button } from '../Button/Button'
import { addDaysJst, isValidDateString, todayInJst } from '../../lib/jst'
import styles from './DateControl.module.css'

interface DateControlProps {
  date: string
  onChange: (date: string) => void
}

export function DateControl({ date, onChange }: DateControlProps) {
  const isToday = date === todayInJst()

  return (
    <div className={styles.control}>
      <Button variant="secondary" onClick={() => onChange(addDaysJst(date, -1))}>
        Previous day
      </Button>
      <input
        type="date"
        className={styles.dateInput}
        value={date}
        aria-label="Date"
        onChange={(event) => {
          const value = event.target.value
          if (isValidDateString(value)) onChange(value)
        }}
      />
      <Button variant="secondary" onClick={() => onChange(addDaysJst(date, 1))}>
        Next day
      </Button>
      <Button
        variant={isToday ? 'primary' : 'secondary'}
        aria-current={isToday ? 'date' : undefined}
        onClick={() => onChange(todayInJst())}
      >
        Today
      </Button>
    </div>
  )
}
