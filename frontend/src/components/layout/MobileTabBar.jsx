// src/components/layout/MobileTabBar.jsx
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  MessageSquare,
  BarChart3,
  GitCompare,
  Bookmark,
} from 'lucide-react'

const TABS = [
  { icon: LayoutDashboard, label: 'Dashboard', to: '/app/dashboard' },
  { icon: MessageSquare,   label: 'Chat',       to: '/app/chat'      },
  { icon: BarChart3,       label: 'Scores',     to: '/app/scorecard' },
  { icon: GitCompare,      label: 'Compare',    to: '/app/compare'   },
  { icon: Bookmark,        label: 'Watchlist',  to: '/app/watchlist' },
]

export default function MobileTabBar() {
  return (
    <nav
      className="
        md:hidden fixed bottom-0 left-0 right-0 z-40
        flex items-center justify-around
        h-16 border-t border-white/[0.07] bg-erebus-surface/95 backdrop-blur-xl
      "
    >
      {TABS.map(({ icon: Icon, label, to }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) => `
            flex flex-col items-center gap-1 px-4 py-2
            text-[10px] font-medium tracking-wide
            transition-all duration-150
            ${isActive
              ? 'text-erebus-gold'
              : 'text-erebus-text-3 hover:text-erebus-text-2'
            }
          `}
        >
          {({ isActive }) => (
            <>
              <div
                className={`
                  w-8 h-8 rounded-lg flex items-center justify-center
                  transition-all duration-150
                  ${isActive ? 'bg-erebus-gold/[0.08]' : ''}
                `}
              >
                <Icon size={17} />
              </div>
              {label}
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}
