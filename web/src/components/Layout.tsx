import { Link, useLocation } from 'react-router-dom'

const NAV_ITEMS = [
  { path: '/', label: 'Market Overview' },
  { path: '/runes', label: 'Rune Dashboard' },
  { path: '/sources', label: 'Sources' },
  { path: '/about-methodology', label: 'Methodology' },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const loc = useLocation()

  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="header-inner">
          <Link to="/" className="logo">
            D2R Market Helper
          </Link>
          <nav className="main-nav">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={loc.pathname === item.path ? 'nav-active' : ''}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="app-main">{children}</main>
      <footer className="app-footer">
        <p>
          D2R Market Helper — Multi-source market intelligence for Diablo II: Resurrected traders.
          Not affiliated with Blizzard Entertainment.
        </p>
      </footer>
    </div>
  )
}
