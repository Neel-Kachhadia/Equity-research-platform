// src/components/layout/Sidebar.jsx
import { NavLink, Link } from 'react-router-dom'
import { useState } from 'react'
import {
  LayoutDashboard,
  MessageSquare,
  BarChart3,
  GitCompare,
  BookOpen,
  Bookmark,
  Clock,
  FileStack,
  Database,
  ScanText,
  Settings,
  ChevronRight,
  Trash2,
  Mic,
} from 'lucide-react'
import UserMenu from '../auth/UserMenu'

const NAV_MAIN = [
  { icon: LayoutDashboard, label: 'Dashboard',         to: '/app/dashboard'        },
  { icon: MessageSquare,   label: 'Chat',               to: '/app/chat'             },
  { icon: BarChart3,       label: 'Scorecards',         to: '/app/scorecard'        },
  { icon: GitCompare,      label: 'Compare',            to: '/app/compare'          },
  { icon: BookOpen,        label: 'Research',           to: '/app/research'         },
  { icon: Mic,             label: 'Audio Intelligence', to: '/app/audio'            },
]

const NAV_LIBRARY = [
  { icon: Bookmark,  label: 'Watchlist', to: '/app/watchlist' },
  { icon: Clock,     label: 'History',   to: '/app/history'   },
  { icon: Database,  label: 'Sources',   to: '/app/files'     },
  { icon: ScanText,  label: 'OCR',       to: '/app/ocr'       },
]

const RECENT = [
  { label: 'HDFC Bank NIM trajectory',     tag: 'chat'    },
  { label: 'Titan vs Kalyan ROE compare',  tag: 'compare' },
  { label: 'Asian Paints FY24 guidance',   tag: 'score'   },
  { label: 'Nifty IT sector risk outlook', tag: 'chat'    },
]

function NavItem({ icon: Icon, label, to }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) => `
        flex items-center gap-2.5 h-9 px-3 mx-2 rounded-md text-[13px] font-medium
        transition-all duration-150
        ${isActive
          ? 'nav-item-active'
          : 'text-erebus-text-3 hover:text-erebus-text-2 hover:bg-erebus-surface-2'
        }
      `}
    >
      <Icon size={15} className="shrink-0" />
      {label}
    </NavLink>
  )
}

export default function Sidebar() {
  const [hoveredRecent, setHoveredRecent] = useState(null)

  return (
    <aside className="hidden md:flex w-56 h-full bg-erebus-surface border-r border-white/[0.07] flex-col shrink-0">

      {/* Brand */}
      <div className="px-4 py-4 border-b border-white/[0.07]">
        <Link to="/" className="flex items-center gap-2 group w-fit">
          <div className="w-7 h-7 rounded-full flex items-center justify-center border border-erebus-gold/50 font-serif text-erebus-gold text-sm group-hover:border-erebus-gold transition-colors bg-erebus-gold/[0.08]">
            E
          </div>
          <span className="font-serif text-[16px] text-erebus-text-1">EREBUS</span>
        </Link>
        <p className="text-[10px] font-mono text-erebus-text-3 mt-1 tracking-wide">Research Workspace</p>
      </div>

      {/* Main nav */}
      <nav className="py-3">
        <p className="px-5 pb-2 text-[10px] font-mono text-erebus-text-3 uppercase tracking-[0.1em]">Main</p>
        {NAV_MAIN.map(item => (
          <NavItem key={item.to} {...item} />
        ))}
      </nav>

      {/* Library nav */}
      <nav className="py-2 border-t border-white/[0.07]">
        <p className="px-5 py-2 text-[10px] font-mono text-erebus-text-3 uppercase tracking-[0.1em]">Library</p>
        {NAV_LIBRARY.map(item => (
          <NavItem key={item.to} {...item} />
        ))}
      </nav>

      {/* Recent threads */}
      <div className="flex-1 overflow-y-auto scrollbar-none py-3 border-t border-white/[0.07]">
        <p className="px-5 pb-2 text-[10px] font-mono text-erebus-text-3 uppercase tracking-[0.1em]">Recent</p>
        {RECENT.map((item, i) => (
          <div
            key={i}
            className="flex items-center gap-2 h-8 px-5 cursor-pointer text-[12px] text-erebus-text-3 hover:text-erebus-text-2 hover:bg-erebus-surface-2 transition-all duration-100 rounded-md mx-1 group"
            onMouseEnter={() => setHoveredRecent(i)}
            onMouseLeave={() => setHoveredRecent(null)}
          >
            <ChevronRight size={10} className="shrink-0 opacity-40" />
            <span className="truncate flex-1">{item.label}</span>
            {hoveredRecent === i && (
              <button className="text-erebus-text-3 hover:text-erebus-red transition-colors p-0.5 shrink-0">
                <Trash2 size={11} />
              </button>
            )}
          </div>
        ))}
      </div>

      {/* User card — click to open dropdown (View Profile / Sign Out) */}
      <div className="px-3 py-3 border-t border-white/[0.07]">
        <UserMenu size="sm" showName={true} />
      </div>
    </aside>
  )
}
