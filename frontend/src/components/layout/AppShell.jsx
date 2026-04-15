// src/components/layout/AppShell.jsx
import { Outlet } from 'react-router-dom'
import Sidebar      from './Sidebar'
import TopBar       from './TopBar'
import MobileTabBar from './MobileTabBar'

export default function AppShell() {
  return (
    <div className="flex h-screen bg-erebus-bg overflow-hidden">
      {/* Sidebar — desktop only */}
      <Sidebar />

      {/* Main area */}
      <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
        <TopBar />
        {/* Page content — scrollable */}
        <main className="flex-1 min-h-0 overflow-y-auto flex flex-col">
          <Outlet />
        </main>
      </div>

      {/* Mobile tab bar */}
      <MobileTabBar />
    </div>
  )
}
