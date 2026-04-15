// src/components/news/NewsWidget.jsx
// Compact news widget — used on Dashboard (top-10 latest) and company pages.
// Props:
//   symbol?   — if provided, fetches company-specific news; otherwise fetches dashboard /news
//   title?    — widget heading (default: "Latest News")
//   limit?    — max articles to show (default: 10)
//   compact?  — condensed single-line rows vs. two-line card layout
import { useState, useEffect, useCallback } from 'react'
import { RefreshCw, ExternalLink, Newspaper, AlertCircle, Clock } from 'lucide-react'
import { getDashboardNews, getCompanyNews, refreshCompanyNews } from '../../services/api'

/* ── Seed helper — calls POST /news/seed directly ─────────────────────────── */
async function triggerSeed() {
  try {
    await fetch('/news/seed', { method: 'POST', headers: { Accept: 'application/json' } })
  } catch { /* non-fatal */ }
}

/* ── helpers ──────────────────────────────────────────────────────────────── */
function relTime(iso) {
  if (!iso) return ''
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60_000)
  if (m < 1)  return 'Just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  const d = Math.floor(h / 24)
  return d === 1 ? 'Yesterday' : `${d}d ago`
}

const SOURCE_COLOR = (src = '') => {
  const s = src.toLowerCase()
  if (s.includes('reuters'))    return '#FF8C00'
  if (s.includes('bloomberg'))  return '#5B9BF0'
  if (s.includes('economic'))   return '#2ECC8A'
  if (s.includes('mint'))       return '#C9A84C'
  return '#6B7280'
}

/* ── Loading skeleton ──────────────────────────────────────────────────────── */
function Skeleton({ rows = 5 }) {
  return (
    <div className="flex flex-col gap-2 p-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex flex-col gap-1.5 py-2 px-3 rounded-lg"
          style={{ background: 'rgba(255,255,255,0.03)' }}>
          <div className="h-2.5 rounded animate-pulse" style={{ background: 'rgba(255,255,255,0.07)', width: `${65 + (i % 3) * 10}%` }} />
          <div className="h-2 rounded animate-pulse" style={{ background: 'rgba(255,255,255,0.04)', width: '40%' }} />
        </div>
      ))}
    </div>
  )
}

/* ── Main component ─────────────────────────────────────────────────────────── */
export default function NewsWidget({
  symbol    = null,
  title     = 'Latest News',
  limit     = 20,
  compact   = false,
}) {
  const [articles,  setArticles]  = useState([])
  const [loading,   setLoading]   = useState(true)
  const [seeding,   setSeeding]   = useState(false)   // true while backend seeds on first empty load
  const [error,     setError]     = useState(null)
  const [refreshing,setRefreshing]= useState(false)

  const load = useCallback(async ({ forceRefresh = false } = {}) => {
    setLoading(true)
    setError(null)
    try {
      const data = symbol
        ? await getCompanyNews(symbol, { limit, refresh: forceRefresh })
        : await getDashboardNews({ limit, refresh: forceRefresh })

      const arts = data.articles || []

      // First load returned empty → call seed endpoint, wait, then retry
      if (arts.length === 0 && !forceRefresh) {
        setSeeding(true)
        setLoading(false)
        await triggerSeed()         // POST /news/seed — runs full seed in ~8s
        // Wait for backend to finish seeding (seed runs synchronously)
        await new Promise(r => setTimeout(r, 9000))
        const seeded = symbol
          ? await getCompanyNews(symbol, { limit, refresh: false })
          : await getDashboardNews({ limit, refresh: false })
        setArticles(seeded.articles || [])
        setSeeding(false)
      } else {
        setArticles(arts)
      }
    } catch (e) {
      const msg = typeof e === 'string' ? e : 'Failed to load news'
      setError(
        msg.includes('503') || msg.includes('unreachable')
          ? 'News DB not available — check RDS connection.'
          : msg
      )
    } finally {
      setLoading(false)
      setSeeding(false)
    }
  }, [symbol, limit])

  useEffect(() => { load() }, [load])

  async function handleRefresh() {
    setRefreshing(true)
    try {
      if (symbol) await refreshCompanyNews(symbol)
      await load({ forceRefresh: true })
    } catch {
      /* silently ignored — load() will set error if needed */
    } finally {
      setRefreshing(false)
    }
  }

  // ── render ─────────────────────────────────────────────────────────────────
  return (
    <div style={{
      background: '#0F1420',
      border: '1px solid rgba(255,255,255,0.10)',
      borderLeft: '3px solid #4A8FE7',
      borderRadius: 10,
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '14px 18px', borderBottom: '1px solid rgba(255,255,255,0.07)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Newspaper size={13} color="#4A8FE7" />
          <span style={{
            fontFamily: "'JetBrains Mono',monospace", fontSize: 10,
            letterSpacing: '0.10em', textTransform: 'uppercase', color: '#4A8FE7', opacity: 0.85,
          }}>{title}</span>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing || loading}
          title="Refresh news"
          style={{
            display: 'flex', alignItems: 'center', gap: 5, background: 'none',
            border: '1px solid rgba(255,255,255,0.10)', borderRadius: 5,
            padding: '4px 9px', cursor: 'pointer', color: '#6B7280',
            fontFamily: "'JetBrains Mono',monospace", fontSize: 9,
            transition: 'color 0.15s',
          }}
          onMouseEnter={e => e.currentTarget.style.color = '#A0A8B8'}
          onMouseLeave={e => e.currentTarget.style.color = '#6B7280'}
        >
          <RefreshCw size={11} style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
          Refresh
        </button>
      </div>

      {/* Body */}
      {loading || seeding ? (
        loading ? (
          <Skeleton rows={Math.min(limit, 5)} />
        ) : (
          // seeding: backend is fetching from Finnhub
          <div style={{ padding: '24px 18px', textAlign: 'center' }}>
            <div style={{ display: 'inline-block', width: 18, height: 18, borderRadius: '50%',
              border: '2px solid rgba(74,143,231,0.2)', borderTopColor: '#4A8FE7',
              animation: 'spin 0.9s linear infinite', marginBottom: 10 }} />
            <p style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: '#5E6880' }}>
              Fetching from Finnhub…
            </p>
          </div>
        )
      ) : error ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '18px 18px',
          color: '#E05C5C', fontFamily: "'Inter',sans-serif", fontSize: 12 }}>
          <AlertCircle size={14} />
          {error}
        </div>
      ) : articles.length === 0 ? (
        <div style={{ padding: '28px 18px', textAlign: 'center' }}>
          <Newspaper size={22} color="rgba(255,255,255,0.12)" style={{ margin: '0 auto 8px' }} />
          <p style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: '#5E6880' }}>
            No news yet — click Refresh to fetch from Finnhub
          </p>
        </div>
      ) : (
        <div style={{ maxHeight: compact ? 320 : 460, overflowY: 'auto' }}>
          {articles.map((a, i) => (
            <a
              key={a.id ?? i}
              href={a.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'flex', alignItems: 'flex-start', gap: 12,
                padding: compact ? '10px 18px' : '13px 18px',
                borderBottom: i < articles.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
                textDecoration: 'none', transition: 'background 0.13s',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              {/* Optional thumbnail */}
              {!compact && a.image_url && (
                <img
                  src={a.image_url}
                  alt=""
                  style={{ width: 44, height: 44, borderRadius: 6, objectFit: 'cover', flexShrink: 0,
                    border: '1px solid rgba(255,255,255,0.08)' }}
                  onError={e => { e.target.style.display = 'none' }}
                />
              )}

              {/* Content */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{
                  fontFamily: "'Inter',sans-serif", fontSize: compact ? 11 : 12,
                  fontWeight: 500, color: '#DCD8CF', lineHeight: 1.45,
                  display: '-webkit-box', WebkitLineClamp: compact ? 1 : 2,
                  WebkitBoxOrient: 'vertical', overflow: 'hidden',
                  marginBottom: 4,
                }}>
                  {a.headline}
                </p>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  {/* Company symbol badge */}
                  {a.company_symbol && a.company_symbol !== 'MARKET' && (
                    <span style={{
                      fontFamily: "'JetBrains Mono',monospace", fontSize: 9, letterSpacing: '0.06em',
                      color: '#C9A84C', background: 'rgba(201,168,76,0.10)',
                      border: '1px solid rgba(201,168,76,0.20)', borderRadius: 3,
                      padding: '1px 5px',
                    }}>{a.company_symbol}</span>
                  )}
                  {/* Source */}
                  {a.source && (
                    <span style={{
                      fontFamily: "'JetBrains Mono',monospace", fontSize: 9,
                      color: SOURCE_COLOR(a.source),
                    }}>{a.source}</span>
                  )}
                  {/* Time */}
                  <span style={{ display: 'flex', alignItems: 'center', gap: 3,
                    fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: '#5E6880' }}>
                    <Clock size={9} />
                    {relTime(a.published_at)}
                  </span>
                </div>
              </div>

              {/* External link icon */}
              <ExternalLink size={11} color="rgba(255,255,255,0.18)" style={{ flexShrink: 0, marginTop: 2 }} />
            </a>
          ))}
        </div>
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg) } }
      `}</style>
    </div>
  )
}
