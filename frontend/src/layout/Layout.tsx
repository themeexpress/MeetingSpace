import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { Button } from '../components/Button/Button'
import styles from './Layout.module.css'

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const { user } = useAuth()

  const linkClassName = ({ isActive }: { isActive: boolean }) =>
    isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink

  return (
    <>
      <NavLink to="/" className={linkClassName} onClick={onNavigate} end>
        Rooms
      </NavLink>
      <NavLink to="/my-bookings" className={linkClassName} onClick={onNavigate}>
        My bookings
      </NavLink>
      {user?.is_staff && (
        <NavLink to="/admin" className={linkClassName} onClick={onNavigate}>
          Admin
        </NavLink>
      )}
    </>
  )
}

export function Layout() {
  const { user, logout } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <>
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      <header className={styles.topBar}>
        <div className={styles.topBarInner}>
          <a href="/" className={styles.appName}>
            MeetingSpace
          </a>
          <nav className={styles.nav} aria-label="Main">
            <NavLinks />
          </nav>
          <button
            type="button"
            className={styles.menuToggle}
            aria-expanded={mobileOpen}
            aria-label="Toggle navigation menu"
            onClick={() => setMobileOpen((open) => !open)}
          >
            ☰
          </button>
          <div className={styles.userMenu}>
            <span className={styles.username}>{user?.username}</span>
            <Button variant="secondary" onClick={() => logout()}>
              Log out
            </Button>
          </div>
        </div>
      </header>
      {mobileOpen && (
        <nav
          className={`${styles.mobilePanel} ${styles.mobilePanelOpen}`}
          aria-label="Main"
        >
          <NavLinks onNavigate={() => setMobileOpen(false)} />
        </nav>
      )}
      <main id="main-content" className={styles.content}>
        <Outlet />
      </main>
    </>
  )
}
