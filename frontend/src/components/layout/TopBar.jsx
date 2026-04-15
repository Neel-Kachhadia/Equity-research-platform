// src/components/layout/TopBar.jsx
import { useLocation } from 'react-router-dom'
import { Bell, Search, ChevronRight } from 'lucide-react'
import UserMenu from '../auth/UserMenu'

const PAGE_META = {
  '/app/dashboard': { title: 'Dashboard',         sub: 'Command Center' },
  '/app/chat':      { title: 'Chat',               sub: 'AI Research Assistant' },
  '/app/scorecard': { title: 'Scorecards',         sub: 'Company Intelligence' },
  '/app/compare':   { title: 'Compare',            sub: 'Peer Analysis Engine' },
  '/app/research':  { title: 'Research Workspace', sub: 'Company Cockpit' },
  '/app/watchlist': { title: 'Watchlist',          sub: 'Portfolio Monitor' },
  '/app/history':   { title: 'History',            sub: 'Research Archive' },
  '/app/files':     { title: 'My Files',           sub: 'Document Library' },
}

export default function TopBar() {
  const location = useLocation()
  const path     = '/' + location.pathname.split('/').slice(1, 3).join('/')
  const meta     = PAGE_META[path] ?? { title: 'EREBUS', sub: '' }

  return (
    <header
      className="h-14 shrink-0 flex items-center justify-between px-5 border-b border-white/[0.07] bg-erebus-surface"
    >
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 min-w-0">
        <span className="text-[11px] font-mono text-erebus-text-3">EREBUS</span>
        <ChevronRight size={12} className="text-erebus-text-3 shrink-0" />
        <span className="text-[13px] font-medium text-erebus-text-1 truncate">{meta.title}</span>
        {meta.sub && (
          <>
            <ChevronRight size={12} className="text-erebus-text-3 shrink-0" />
            <span className="text-[12px] font-mono text-erebus-text-3 hidden sm:block">{meta.sub}</span>
          </>
        )}
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-2 shrink-0">
        {/* Search trigger */}
        <button
          className="
            hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md
            text-[12px] font-mono text-erebus-text-3
            border border-white/[0.08] bg-erebus-bg
            hover:border-erebus-gold/30 hover:text-erebus-text-2
            transition-all duration-150
          "
        >
          <Search size={12} />
          Search
          <span className="hidden md:inline text-erebus-text-3 ml-1">⌘K</span>
        </button>

        {/* Notification bell */}
        <button
          className="
            relative w-8 h-8 rounded-md flex items-center justify-center
            text-erebus-text-3 hover:text-erebus-text-1
            hover:bg-erebus-surface-2 transition-all duration-150
          "
        >
          <Bell size={15} />
          <span
            className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-erebus-gold animate-[pulse-dot_2s_infinite]"
          />
        </button>

        {/* User avatar → dropdown with View Profile + Sign Out */}
        <UserMenu size="md" />
      </div>
    </header>
  )
}
