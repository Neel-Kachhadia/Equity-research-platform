// src/pages/app/HistoryPage.jsx
import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  Clock, MessageSquare, BarChart3, GitCompare,
  ArrowRight, Trash2, RefreshCw, X, AlertCircle, Loader2, Trash,
} from 'lucide-react'
import { listSessions, deleteSession, clearAllSessions } from '../../services/api'

// ── Constants ─────────────────────────────────────────────────────────────────

const TYPE_ICONS = { chat: MessageSquare, score: BarChart3, compare: GitCompare }
const TYPE_META  = {
  chat:    { label: 'Chat',    accent: '#4A8FE7' },
  score:   { label: 'Score',   accent: '#2ECC8A' },
  compare: { label: 'Compare', accent: '#C9A84C' },
}

function relativeTime(iso) {
  if (!iso) return ''
  const diff = Date.now() - new Date(iso).getTime()
  const mins  = Math.floor(diff / 60_000)
  if (mins < 1)  return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days === 1) return 'Yesterday'
  if (days < 7)  return `${days} days ago`
  return new Date(iso).toLocaleDateString()
}

// ── Confirm clear-all dialog ──────────────────────────────────────────────────

function ConfirmClearModal({ onClose, onConfirm, loading }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(4px)' }}
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div
        className="w-full max-w-sm rounded-2xl p-6 shadow-2xl"
        style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
      >
        <div className="flex items-center gap-3 mb-3">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center"
            style={{ background: '#EF444418', border: '1px solid #EF444430' }}>
            <Trash size={15} style={{ color: '#EF4444' }} />
          </div>
          <h2 className="font-serif text-[18px] text-erebus-text-1">Clear All History</h2>
        </div>
        <p className="text-[13px] text-erebus-text-3 mb-5">
          This will permanently delete every tracked session. This action cannot be undone.
        </p>
        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 py-2 rounded-lg text-[13px] text-erebus-text-3 hover:text-erebus-text-1 transition-colors"
            style={{ border: '1px solid var(--border)' }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="flex-1 py-2 rounded-lg text-[13px] font-medium flex items-center justify-center gap-2 transition-opacity"
            style={{ background: '#EF4444', color: '#fff', opacity: loading ? 0.7 : 1 }}
          >
            {loading ? <Loader2 size={13} className="animate-spin" /> : <Trash size={13} />}
            Delete all
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function HistoryPage() {
  const [sessions,   setSessions]   = useState([])
  const [loading,    setLoading]    = useState(true)
  const [error,      setError]      = useState(null)
  const [clearModal, setClearModal] = useState(false)
  const [clearing,   setClearing]   = useState(false)
  const [deletingId, setDeletingId] = useState(null)

  // ── Load ──────────────────────────────────────────────────────────────────
  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listSessions()
      setSessions(data.sessions)
    } catch (e) {
      const msg = typeof e === 'string' ? e : 'Failed to load history'
      // 503 = DB not yet reachable; show actionable message
      setError(msg.includes('whitelist') || msg.includes('unreachable')
        ? 'Database not reachable — whitelist your IP on port 5432 in the RDS security group, then refresh.'
        : msg)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  // ── Delete one ────────────────────────────────────────────────────────────
  async function handleDelete(id) {
    setDeletingId(id)
    try {
      await deleteSession(id)
      setSessions(prev => prev.filter(s => s.id !== id))
    } catch (e) {
      setError(typeof e === 'string' ? e : 'Delete failed')
    } finally {
      setDeletingId(null)
    }
  }

  // ── Clear all ─────────────────────────────────────────────────────────────
  async function handleClearAll() {
    setClearing(true)
    try {
      await clearAllSessions()
      setSessions([])
      setClearModal(false)
    } catch (e) {
      setError(typeof e === 'string' ? e : 'Clear failed')
    } finally {
      setClearing(false)
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="h-full overflow-y-auto scrollbar-none">
      <div className="max-w-3xl mx-auto px-6 pt-8 pb-16">

        {/* Header */}
        <div className="flex items-center justify-between mb-7">
          <div>
            <h1 className="font-serif text-[28px] text-erebus-text-1 mb-1">Research History</h1>
            <p className="text-[12px] font-mono text-erebus-text-3">
              {loading
                ? 'Loading…'
                : `${sessions.length} session${sessions.length !== 1 ? 's' : ''} · Auto-tracked`}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* Refresh */}
            <button
              onClick={load}
              disabled={loading}
              title="Refresh"
              className="p-2 rounded-lg text-erebus-text-3 hover:text-erebus-text-1 transition-colors"
              style={{ border: '1px solid var(--border)' }}
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
            {/* Clear all */}
            {sessions.length > 0 && (
              <button
                onClick={() => setClearModal(true)}
                title="Clear all history"
                className="p-2 rounded-lg transition-colors"
                style={{ border: '1px solid var(--border)', color: '#EF4444' }}
              >
                <Trash size={14} />
              </button>
            )}
          </div>
        </div>

        {/* Error banner */}
        {error && (
          <div
            className="flex items-center gap-2 px-4 py-3 mb-4 rounded-xl text-[13px]"
            style={{ background: '#EF444418', border: '1px solid #EF444430', color: '#EF4444' }}
          >
            <AlertCircle size={14} />
            {error}
            <button onClick={() => setError(null)} className="ml-auto">
              <X size={13} />
            </button>
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map(i => (
              <div
                key={i}
                className="h-[62px] rounded-xl animate-pulse"
                style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
              />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && sessions.length === 0 && !error && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
              style={{ background: '#4A8FE710', border: '1px solid #4A8FE720' }}
            >
              <Clock size={22} style={{ color: '#4A8FE7' }} />
            </div>
            <p className="text-[15px] text-erebus-text-1 mb-1">No sessions yet</p>
            <p className="text-[12px] font-mono text-erebus-text-3">
              Your research activity will be automatically tracked here.
            </p>
          </div>
        )}

        {/* Sessions list */}
        {!loading && sessions.length > 0 && (
          <div className="space-y-2">
            {sessions.map(s => {
              const Icon = TYPE_ICONS[s.session_type] || MessageSquare
              const meta = TYPE_META[s.session_type]  || TYPE_META.chat
              const isDeleting = deletingId === s.id
              return (
                <div
                  key={s.id}
                  className="flex items-center gap-4 px-5 py-4 rounded-xl group hover:bg-erebus-surface transition-colors"
                  style={{
                    border: '1px solid var(--border)',
                    opacity: isDeleting ? 0.4 : 1,
                    transition: 'opacity 0.2s',
                  }}
                >
                  {/* Icon */}
                  <div
                    className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
                    style={{ background: `${meta.accent}12`, border: `1px solid ${meta.accent}20` }}
                  >
                    <Icon size={15} style={{ color: meta.accent }} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-medium text-erebus-text-1 truncate mb-0.5">
                      {s.title}
                    </p>
                    <div className="flex items-center gap-2">
                      <span
                        className="text-[10px] font-mono px-1.5 py-0.5 rounded"
                        style={{
                          background: `${meta.accent}10`,
                          color: meta.accent,
                          border: `1px solid ${meta.accent}18`,
                        }}
                      >
                        {meta.label}
                      </span>
                      {s.sub && (
                        <span className="text-[11px] font-mono text-erebus-text-3 truncate">
                          {s.sub}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Time + actions */}
                  <div className="flex items-center gap-3 shrink-0">
                    <div className="flex items-center gap-1.5 text-[11px] font-mono text-erebus-text-3">
                      <Clock size={11} />
                      {relativeTime(s.created_at)}
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      {/* Navigate to research page if ticker */}
                      {s.ticker && (
                        <Link
                          to={`/app/research/${s.ticker.toLowerCase()}`}
                          className="p-1.5 text-erebus-text-3 hover:text-erebus-gold transition-colors rounded"
                          title="Open in Research"
                        >
                          <ArrowRight size={13} />
                        </Link>
                      )}
                      {/* Delete */}
                      <button
                        onClick={() => handleDelete(s.id)}
                        disabled={isDeleting}
                        className="p-1.5 text-erebus-text-3 hover:text-red-400 transition-colors rounded"
                        title="Remove from history"
                      >
                        {isDeleting
                          ? <Loader2 size={12} className="animate-spin" />
                          : <Trash2 size={13} />
                        }
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Clear-all confirm */}
      {clearModal && (
        <ConfirmClearModal
          onClose={() => setClearModal(false)}
          onConfirm={handleClearAll}
          loading={clearing}
        />
      )}
    </div>
  )
}
