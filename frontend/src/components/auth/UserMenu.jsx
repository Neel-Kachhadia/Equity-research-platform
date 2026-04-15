// src/components/auth/UserMenu.jsx
// Reusable avatar + dropdown: "View Profile" and "Sign Out"
// Used by both Sidebar (bottom) and TopBar (top-right)

import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { User, LogOut, ChevronDown } from 'lucide-react'
import { useAuthStore } from '../../store/useAuthStore'
import ProfileModal from './ProfileModal'

// Derive initials from a name string
export function initials(name = '') {
  return name.split(' ').filter(Boolean).slice(0, 2).map(w => w[0].toUpperCase()).join('') || 'U'
}

/**
 * Props:
 *   size      — 'sm' (28px, for sidebar) | 'md' (32px, for topbar)
 *   showName  — show the name text next to the avatar (sidebar mode)
 */
export default function UserMenu({ size = 'md', showName = false }) {
  const [open,        setOpen]        = useState(false)
  const [showProfile, setShowProfile] = useState(false)

  const dropdownRef = useRef(null)
  const navigate    = useNavigate()
  const logout      = useAuthStore(s => s.logout)
  const user        = useAuthStore(s => s.user)

  const dim    = size === 'sm' ? 28 : 32
  const ini    = initials(user?.name)
  const avatar = user?.avatar  // base64 or URL set by ProfileModal

  // Close dropdown when clicking outside
  useEffect(() => {
    function handle(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [])

  function handleSignOut() {
    setOpen(false)
    logout()
    navigate('/', { replace: true })
  }

  return (
    <>
      {/* Trigger */}
      <div ref={dropdownRef} style={{ position: 'relative' }}>
        <button
          onClick={() => setOpen(v => !v)}
          style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            background: 'none', border: 'none', cursor: 'pointer',
            padding: showName ? '6px 8px' : '0',
            borderRadius: '8px',
            transition: 'background 0.15s',
          }}
          onMouseEnter={e => { if (showName) e.currentTarget.style.background = 'rgba(255,255,255,0.04)' }}
          onMouseLeave={e => { if (showName) e.currentTarget.style.background = 'none' }}
        >
          {/* Avatar circle */}
          <div style={{
            width: dim, height: dim, borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: avatar ? 'transparent' : 'rgba(201,168,76,0.08)',
            border: '1px solid rgba(201,168,76,0.25)',
            overflow: 'hidden', flexShrink: 0,
          }}>
            {avatar
              ? <img src={avatar} alt="avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              : <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '11px', fontWeight: 600, color: '#C9A84C' }}>{ini}</span>
            }
          </div>

          {/* Name + chevron (sidebar mode) */}
          {showName && (
            <>
              <div style={{ textAlign: 'left', flex: 1, minWidth: 0 }}>
                <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 500, color: '#E8E4DA', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {user?.name || 'Analyst'}
                </p>
                <p style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: 'rgba(255,255,255,0.3)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {user?.email || ''}
                </p>
              </div>
              <ChevronDown size={12} style={{ color: 'rgba(255,255,255,0.3)', flexShrink: 0, transform: open ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.2s' }} />
            </>
          )}
        </button>

        {/* Dropdown */}
        {open && (
          <div style={{
            position: 'absolute',
            bottom: showName ? 'calc(100% + 6px)' : 'auto',
            top:    showName ? 'auto' : 'calc(100% + 8px)',
            right:  showName ? 0 : 0,
            left:   showName ? 0 : 'auto',
            width:  '188px',
            background: '#161920',
            border: '1px solid rgba(255,255,255,0.09)',
            borderRadius: '10px',
            boxShadow: '0 12px 40px rgba(0,0,0,0.55)',
            zIndex: 999,
            overflow: 'hidden',
          }}>
            {/* User info header */}
            <div style={{ padding: '12px 14px', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
              <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', fontWeight: 600, color: '#E8E4DA', marginBottom: '2px' }}>
                {user?.name || 'Analyst'}
              </p>
              <p style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: 'rgba(255,255,255,0.3)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user?.email || ''}
              </p>
            </div>

            {/* Menu items */}
            <div style={{ padding: '6px' }}>
              <DropItem
                icon={<User size={13} />}
                label="View profile"
                onClick={() => { setOpen(false); setShowProfile(true) }}
              />
              <DropItem
                icon={<LogOut size={13} />}
                label="Sign out"
                danger
                onClick={handleSignOut}
              />
            </div>
          </div>
        )}
      </div>

      {/* Profile modal */}
      {showProfile && <ProfileModal onClose={() => setShowProfile(false)} />}
    </>
  )
}

function DropItem({ icon, label, onClick, danger }) {
  const [hov, setHov] = useState(false)
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        width: '100%', display: 'flex', alignItems: 'center', gap: '9px',
        padding: '8px 10px', borderRadius: '6px', border: 'none',
        background: hov ? (danger ? 'rgba(180,60,60,0.15)' : 'rgba(255,255,255,0.05)') : 'none',
        color: hov
          ? (danger ? '#E06060' : '#E8E4DA')
          : (danger ? 'rgba(220,100,100,0.7)' : 'rgba(255,255,255,0.55)'),
        cursor: 'pointer', textAlign: 'left',
        fontFamily: 'Inter, sans-serif', fontSize: '13px',
        transition: 'all 0.15s',
      }}
    >
      {icon}
      {label}
    </button>
  )
}
