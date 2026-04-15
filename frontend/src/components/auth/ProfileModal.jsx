// src/components/auth/ProfileModal.jsx
// Editable profile modal — name, email, role, avatar upload
// Saves to useAuthStore (client-side persistence via Zustand persist)

import { useState, useRef } from 'react'
import { X, Camera, Check, AlertCircle } from 'lucide-react'
import { useAuthStore } from '../../store/useAuthStore'

const ROLES = ['Retail Analyst', 'Fund Manager', 'Research Intern', 'Quant Analyst', 'Other']

export default function ProfileModal({ onClose }) {
  const user       = useAuthStore(s => s.user)
  const updateUser = useAuthStore(s => s.updateUser)

  const [name,    setName]    = useState(user?.name  || '')
  const [email,   setEmail]   = useState(user?.email || '')
  const [role,    setRole]    = useState(user?.role  || 'Retail Analyst')
  const [avatar,  setAvatar]  = useState(user?.avatar || null)
  const [saved,   setSaved]   = useState(false)
  const [error,   setError]   = useState('')
  const [avatarHov, setAvatarHov] = useState(false)

  const fileRef = useRef(null)

  function handleAvatarChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.type.startsWith('image/')) { setError('Please select an image file'); return }
    if (file.size > 2 * 1024 * 1024) { setError('Image must be under 2 MB'); return }

    const reader = new FileReader()
    reader.onload = (ev) => setAvatar(ev.target.result)
    reader.readAsDataURL(file)
    setError('')
  }

  function handleSave() {
    if (!name.trim()) { setError('Name is required'); return }
    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Enter a valid email address'); return
    }
    updateUser({ name: name.trim(), email: email.trim(), role, avatar })
    setSaved(true)
    setError('')
    setTimeout(() => setSaved(false), 2500)
  }

  // Initials fallback
  const ini = (name || 'U').split(' ').filter(Boolean).slice(0, 2).map(w => w[0].toUpperCase()).join('')

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 2000,
      background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '20px',
    }} onClick={e => { if (e.target === e.currentTarget) onClose() }}>

      <div style={{
        width: '100%', maxWidth: '460px',
        background: '#111419',
        border: '1px solid rgba(255,255,255,0.09)',
        borderRadius: '16px',
        boxShadow: '0 24px 80px rgba(0,0,0,0.7)',
        overflow: 'hidden',
      }}>

        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '20px 24px 16px',
          borderBottom: '1px solid rgba(255,255,255,0.07)',
        }}>
          <div>
            <h2 style={{ fontFamily: 'DM Serif Display, serif', fontSize: '20px', color: '#E8E4DA', margin: 0 }}>
              Your Profile
            </h2>
            <p style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: 'rgba(255,255,255,0.3)', marginTop: '3px', letterSpacing: '0.08em' }}>
              EREBUS · RESEARCH WORKSPACE
            </p>
          </div>
          <button onClick={onClose} style={{
            width: 32, height: 32, borderRadius: '8px', border: 'none',
            background: 'rgba(255,255,255,0.05)', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'rgba(255,255,255,0.5)', transition: 'all 0.15s',
          }}
            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.10)'; e.currentTarget.style.color = '#fff' }}
            onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; e.currentTarget.style.color = 'rgba(255,255,255,0.5)' }}
          >
            <X size={15} />
          </button>
        </div>

        <div style={{ padding: '24px' }}>

          {/* Avatar section */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '28px' }}>
            {/* Avatar circle */}
            <div
              style={{ position: 'relative', cursor: 'pointer', flexShrink: 0 }}
              onMouseEnter={() => setAvatarHov(true)}
              onMouseLeave={() => setAvatarHov(false)}
              onClick={() => fileRef.current?.click()}
            >
              <div style={{
                width: 72, height: 72, borderRadius: '50%',
                background: avatar ? 'transparent' : 'rgba(201,168,76,0.10)',
                border: `2px solid ${avatarHov ? 'rgba(201,168,76,0.7)' : 'rgba(201,168,76,0.25)'}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                overflow: 'hidden', transition: 'border-color 0.2s',
              }}>
                {avatar
                  ? <img src={avatar} alt="avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  : <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '22px', fontWeight: 700, color: '#C9A84C' }}>{ini}</span>
                }
              </div>
              {/* Camera overlay */}
              <div style={{
                position: 'absolute', inset: 0, borderRadius: '50%',
                background: 'rgba(0,0,0,0.55)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                opacity: avatarHov ? 1 : 0, transition: 'opacity 0.2s',
              }}>
                <Camera size={18} style={{ color: '#C9A84C' }} />
              </div>
            </div>

            <div>
              <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '14px', fontWeight: 600, color: '#E8E4DA', marginBottom: '4px' }}>
                Profile Photo
              </p>
              <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', color: 'rgba(255,255,255,0.35)', lineHeight: 1.55 }}>
                JPG, PNG or GIF · Max 2 MB
              </p>
              <button
                onClick={() => fileRef.current?.click()}
                style={{
                  marginTop: '8px', fontFamily: 'JetBrains Mono, monospace', fontSize: '11px',
                  color: '#C9A84C', background: 'none', border: '1px solid rgba(201,168,76,0.35)',
                  borderRadius: '5px', padding: '4px 12px', cursor: 'pointer', letterSpacing: '0.06em',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(201,168,76,0.08)' }}
                onMouseLeave={e => { e.currentTarget.style.background = 'none' }}
              >
                {avatar ? 'Change photo' : 'Upload photo'}
              </button>
            </div>
            <input ref={fileRef} type="file" accept="image/*" onChange={handleAvatarChange} style={{ display: 'none' }} />
          </div>

          {/* Fields */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

            {/* Full name */}
            <Field label="Full name">
              <input
                value={name}
                onChange={e => { setName(e.target.value); setError('') }}
                placeholder="Your full name"
                style={inputStyle}
                onFocus={e => e.target.style.borderColor = 'rgba(201,168,76,0.5)'}
                onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.10)'}
              />
            </Field>

            {/* Email */}
            <Field label="Email address">
              <input
                type="email"
                value={email}
                onChange={e => { setEmail(e.target.value); setError('') }}
                placeholder="you@example.com"
                style={inputStyle}
                onFocus={e => e.target.style.borderColor = 'rgba(201,168,76,0.5)'}
                onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.10)'}
              />
            </Field>

            {/* Role */}
            <Field label="Role">
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '7px' }}>
                {ROLES.map(r => (
                  <RoleChip key={r} label={r} active={role === r} onClick={() => setRole(r)} />
                ))}
              </div>
            </Field>

          </div>

          {/* Error / success messages */}
          {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '16px', padding: '10px 14px', background: 'rgba(180,60,60,0.10)', border: '1px solid rgba(180,60,60,0.25)', borderRadius: '8px' }}>
              <AlertCircle size={13} style={{ color: '#E06060', flexShrink: 0 }} />
              <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', color: '#E06060' }}>{error}</p>
            </div>
          )}
          {saved && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '16px', padding: '10px 14px', background: 'rgba(46,130,90,0.10)', border: '1px solid rgba(46,130,90,0.25)', borderRadius: '8px' }}>
              <Check size={13} style={{ color: '#5AAE85', flexShrink: 0 }} />
              <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', color: '#5AAE85' }}>Profile updated successfully</p>
            </div>
          )}

          {/* Footer actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '24px' }}>
            <GhostBtn onClick={onClose}>Cancel</GhostBtn>
            <GoldBtn onClick={handleSave}>Save changes</GoldBtn>
          </div>

        </div>
      </div>
    </div>
  )
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function Field({ label, children }) {
  return (
    <div>
      <label style={{ display: 'block', fontFamily: 'Inter, sans-serif', fontSize: '12px', color: 'rgba(255,255,255,0.45)', marginBottom: '7px', letterSpacing: '0.02em' }}>
        {label}
      </label>
      {children}
    </div>
  )
}

function RoleChip({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '5px 14px', borderRadius: '20px', border: `1px solid ${active ? 'rgba(201,168,76,0.5)' : 'rgba(255,255,255,0.10)'}`,
        background: active ? 'rgba(201,168,76,0.10)' : 'transparent',
        color: active ? '#C9A84C' : 'rgba(255,255,255,0.4)',
        fontFamily: 'Inter, sans-serif', fontSize: '12px', cursor: 'pointer',
        transition: 'all 0.15s',
      }}
    >
      {label}
    </button>
  )
}

function GhostBtn({ children, onClick }) {
  const [hov, setHov] = useState(false)
  return (
    <button onClick={onClick}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        padding: '9px 20px', borderRadius: '8px', cursor: 'pointer',
        border: '1px solid rgba(255,255,255,0.12)',
        background: hov ? 'rgba(255,255,255,0.06)' : 'transparent',
        color: 'rgba(255,255,255,0.55)', fontFamily: 'Inter, sans-serif', fontSize: '13px',
        transition: 'all 0.15s',
      }}
    >
      {children}
    </button>
  )
}

function GoldBtn({ children, onClick }) {
  const [hov, setHov] = useState(false)
  return (
    <button onClick={onClick}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        padding: '9px 22px', borderRadius: '8px', cursor: 'pointer', border: 'none',
        background: hov ? '#DFC06A' : '#C9A84C',
        color: '#09090f', fontFamily: 'Inter, sans-serif', fontSize: '13px', fontWeight: 600,
        boxShadow: hov ? '0 4px 20px rgba(201,168,76,0.3)' : 'none',
        transition: 'all 0.2s',
      }}
    >
      {children}
    </button>
  )
}

const inputStyle = {
  width: '100%', background: '#0D1117',
  border: '1px solid rgba(255,255,255,0.10)', borderRadius: '8px',
  padding: '10px 14px', color: '#E8E4DA',
  fontFamily: 'Inter, sans-serif', fontSize: '13px',
  outline: 'none', transition: 'border-color 0.2s', boxSizing: 'border-box',
}
