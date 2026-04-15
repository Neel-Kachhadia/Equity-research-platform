// src/pages/app/ComparePage.jsx
import { useState, useRef, useEffect } from 'react'
import {
  Search, X, Plus, ArrowRight, GitCompare,
  TrendingUp, TrendingDown, AlertCircle, Loader2,
  Trophy, ShieldCheck, Zap, BarChart2, RefreshCw,
  Info, FileText,
} from 'lucide-react'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  Tooltip as ReTooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Cell, CartesianGrid,
} from 'recharts'
import { compareCompanies, fetchCompanies, listS3Files, generateDownloadUrl } from '../../services/api'
import FileViewer from '../../components/ui/FileViewer'

/* ── Constants ───────────────────────────────────────────────────── */
const PALETTE = ['#C9A84C', '#4A8FE7']

const CAT_ICONS = {
  performance: Trophy,
  risk:        ShieldCheck,
  alpha:       Zap,
  technical:   BarChart2,
}

/* ── Helpers ─────────────────────────────────────────────────────── */
function fmt(v, unit = '', dp = 1) {
  if (v == null) return '—'
  const n = parseFloat(v)
  if (Number.isNaN(n)) return String(v)
  return `${n.toFixed(dp)}${unit}`
}

function pct(v) { return fmt(v, '%') }

/* ── Data quality badge ──────────────────────────────────────────── */
function DqBadge({ score }) {
  if (score == null) return null
  const pct = Math.round(score * 100)
  const color = pct >= 70 ? '#4ade80' : pct >= 40 ? '#facc15' : '#f87171'
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono border"
      style={{ color, borderColor: `${color}40`, background: `${color}10` }}
    >
      <span className="w-1 h-1 rounded-full shrink-0" style={{ background: color }} />
      DQ {pct}%
    </span>
  )
}

/* ── Warnings panel ──────────────────────────────────────────────── */
function WarningsPanel({ warnings }) {
  if (!warnings?.length) return null
  return (
    <div className="elevated rounded-xl p-4 border border-yellow-500/20 bg-yellow-500/[0.04]">
      <p className="text-[10px] font-mono text-yellow-400/70 uppercase tracking-wider mb-2">
        Data Quality Warnings
      </p>
      <ul className="space-y-1">
        {warnings.map((w, i) => (
          <li key={i} className="flex items-start gap-2">
            <Info size={11} className="text-yellow-400/60 mt-0.5 shrink-0" />
            <span className="text-[12px] text-yellow-300/80">{w}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

/* ── Company slot placeholder ────────────────────────────────────── */
function EmptySlot({ index, onSelect, disabled, universe, loadingUniverse }) {
  const [query, setQuery] = useState('')
  const [open,  setOpen]  = useState(false)
  const inputRef          = useRef(null)

  const filtered = universe
    .filter(c => c.ticker.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 10)

  const LABELS = ['Add first company', 'Add second company']

  // Allow submitting any free-text ticker even if not in the discovered list
  function handleFreeEntry(e) {
    if (e.key === 'Enter' && query.trim()) {
      onSelect(query.trim().toUpperCase())
      setOpen(false)
      setQuery('')
    }
  }

  return (
    <div className="relative">
      <button
        disabled={disabled}
        onClick={() => { setOpen(true); setTimeout(() => inputRef.current?.focus(), 50) }}
        className="w-full elevated rounded-xl p-5 border border-dashed border-white/[0.12] hover:border-erebus-gold/30 hover:bg-white/[0.02] transition-all duration-200 group text-left disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg border border-dashed border-white/[0.12] group-hover:border-erebus-gold/30 flex items-center justify-center transition-colors">
            <Plus size={15} className="text-erebus-text-3 group-hover:text-erebus-gold transition-colors" />
          </div>
          <div>
            <p className="text-[13px] font-medium text-erebus-text-3 group-hover:text-erebus-text-2 transition-colors">
              {LABELS[index] ?? 'Add company'}
            </p>
            <p className="text-[11px] font-mono text-erebus-text-3 mt-0.5">
              {loadingUniverse ? 'Loading S3 companies…' : 'Search or type any ticker → Enter'}
            </p>
          </div>
        </div>
      </button>

      {open && (
        <div className="absolute top-0 left-0 right-0 z-30 elevated rounded-xl border border-erebus-gold/30 overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-white/[0.07]">
            <Search size={13} className="text-erebus-text-3 shrink-0" />
            <input
              ref={inputRef}
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={handleFreeEntry}
              onBlur={() => setTimeout(() => { setOpen(false); setQuery('') }, 150)}
              placeholder="Search S3 ticker or type one → Enter…"
              className="flex-1 bg-transparent text-[13px] text-erebus-text-1 outline-none"
            />
            <button onClick={() => { setOpen(false); setQuery('') }} className="text-erebus-text-3 hover:text-erebus-text-1">
              <X size={13} />
            </button>
          </div>
          <div className="max-h-64 overflow-y-auto scrollbar-none">
            {loadingUniverse && (
              <div className="flex items-center gap-2 px-4 py-3 text-[12px] text-erebus-text-3">
                <Loader2 size={12} className="animate-spin" /> Loading from S3…
              </div>
            )}
            {!loadingUniverse && filtered.map(c => (
              <button
                key={c.ticker}
                onMouseDown={() => { onSelect(c.ticker); setOpen(false); setQuery('') }}
                className="w-full flex items-center justify-between gap-3 px-4 py-2.5 hover:bg-erebus-surface-2 transition-colors text-left"
              >
                <span className="ticker text-erebus-gold text-[12px]">{c.ticker}</span>
                <span className="text-[10px] font-mono text-erebus-text-3 shrink-0">S3</span>
              </button>
            ))}
            {!loadingUniverse && filtered.length === 0 && query.trim() && (
              <div className="px-4 py-3 text-[12px] text-erebus-text-3">
                <p>No S3 match for "<span className="text-erebus-gold">{query}</span>"</p>
                <p className="text-[11px] mt-1 text-erebus-text-3/70">
                  Press <kbd className="px-1 py-0.5 rounded bg-white/[0.06] font-mono text-[10px]">Enter</kbd> to use this ticker anyway
                </p>
              </div>
            )}
            {!loadingUniverse && filtered.length === 0 && !query.trim() && (
              <p className="px-4 py-3 text-[12px] text-erebus-text-3 text-center">Start typing to search or Enter a ticker</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Filled slot ─────────────────────────────────────────────────── */
function FilledSlot({ ticker, index, onRemove, disabled }) {
  const color = PALETTE[index % PALETTE.length]

  return (
    <div className="elevated rounded-xl p-5 relative" style={{ borderColor: `${color}30` }}>
      <button
        disabled={disabled}
        onClick={() => onRemove(ticker)}
        className="absolute top-3 right-3 text-erebus-text-3 hover:text-red-400 transition-colors disabled:opacity-40"
      >
        <X size={14} />
      </button>
      <div className="flex items-center gap-3 mb-3">
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center text-[11px] font-mono font-semibold"
          style={{ background: `${color}18`, color }}
        >
          {ticker.slice(0, 3).toUpperCase()}
        </div>
        <div>
          <p className="ticker text-[13px]" style={{ color }}>{ticker}</p>
          <p className="text-[11px] text-erebus-text-3">S3 · NSE/BSE</p>
        </div>
      </div>
      <p className="text-[12px] text-erebus-text-2 truncate">{ticker}</p>
    </div>
  )
}

/* ── Winner banner ───────────────────────────────────────────────── */
function WinnerBanner({ summary, confidence, idA, idB }) {
  const { winner, comparison_confidence, category_winners } = summary
  const isTie = winner === 'tie'

  return (
    <div className="elevated rounded-xl p-5 border border-erebus-gold/20">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <p className="text-[10px] font-mono text-erebus-text-3 uppercase tracking-widest mb-1">EREBUS Verdict</p>
          <p className="text-[22px] font-serif text-erebus-gold leading-none">
            {isTie ? 'Too Close to Call' : `${winner} leads`}
          </p>
          <div className="flex items-center gap-3 mt-1.5">
            <p className="text-[12px] font-mono text-erebus-text-3">
              {isTie
                ? 'Both companies score similarly'
                : `${Math.round((comparison_confidence ?? 0.5) * 100)}% score separation`}
            </p>
            {confidence != null && (
              <DqBadge score={confidence} />
            )}
          </div>
          {confidence != null && confidence < 0.5 && (
            <p className="text-[11px] font-mono text-yellow-400/70 mt-1">
              ⚠ Low data confidence — results indicative only
            </p>
          )}
        </div>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(category_winners).map(([cat, w]) => {
            const Icon = CAT_ICONS[cat] || BarChart2
            const isTieCat = w === 'tie'
            return (
              <div key={cat} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06]">
                <Icon size={10} className="text-erebus-text-3 shrink-0" />
                <span className="text-[10px] font-mono text-erebus-text-3 capitalize w-20 truncate">{cat}</span>
                <span className={`text-[10px] font-mono font-semibold ml-auto ${isTieCat ? 'text-erebus-text-3' : 'text-erebus-gold'}`}>
                  {isTieCat ? 'Tie' : w}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

/* ── Radar chart ─────────────────────────────────────────────────── */
function CompareRadar({ chartData, idA, idB }) {
  if (!chartData?.labels?.length) return null

  const data = chartData.labels.map((label, i) => ({
    subject: label,
    [idA]:   Math.round((chartData.company_a?.[i] ?? 0) * 100),
    [idB]:   Math.round((chartData.company_b?.[i] ?? 0) * 100),
  }))

  return (
    <div className="elevated rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <p className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-wider">Multi-Dimension Radar</p>
        <div className="flex items-center gap-4">
          {[idA, idB].map((id, i) => (
            <div key={id} className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full" style={{ background: PALETTE[i] }} />
              <span className="text-[11px] font-mono text-erebus-text-3">{id}</span>
            </div>
          ))}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={270}>
        <RadarChart data={data}>
          <PolarGrid stroke="rgba(255,255,255,0.06)" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: '#4E5262', fontSize: 10, fontFamily: 'JetBrains Mono' }} />
          <Radar name={idA} dataKey={idA} stroke={PALETTE[0]} fill={PALETTE[0]} fillOpacity={0.10} strokeWidth={2} isAnimationActive animationDuration={800} />
          <Radar name={idB} dataKey={idB} stroke={PALETTE[1]} fill={PALETTE[1]} fillOpacity={0.10} strokeWidth={2} isAnimationActive animationDuration={800} />
          <ReTooltip
            contentStyle={{ background: '#151921', border: '1px solid rgba(255,255,255,0.10)', borderRadius: '8px', fontSize: '12px', fontFamily: 'JetBrains Mono', color: '#EEE9E0' }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

/* ── Scores bar chart ────────────────────────────────────────────── */
function ScoresChart({ scores, idA, idB }) {
  const data = Object.entries(scores).map(([cat, vals]) => ({
    name:  cat.charAt(0).toUpperCase() + cat.slice(1),
    [idA]: Math.round((vals[idA] ?? 0.5) * 100),
    [idB]: Math.round((vals[idB] ?? 0.5) * 100),
  }))

  return (
    <div className="elevated rounded-xl p-6">
      <p className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-wider mb-4">Dimension Scores (0–100)</p>
      <ResponsiveContainer width="100%" height={150}>
        <BarChart data={data} barCategoryGap="30%">
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis dataKey="name" tick={{ fill: '#4E5262', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} />
          <YAxis domain={[0, 100]} tick={{ fill: '#4E5262', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} />
          <ReTooltip
            contentStyle={{ background: '#151921', border: '1px solid rgba(255,255,255,0.10)', borderRadius: '8px', fontSize: '12px', fontFamily: 'JetBrains Mono', color: '#EEE9E0' }}
          />
          <Bar dataKey={idA} name={idA} fill={PALETTE[0]} radius={[3,3,0,0]} />
          <Bar dataKey={idB} name={idB} fill={PALETTE[1]} radius={[3,3,0,0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/* ── Metric table ────────────────────────────────────────────────── */
const METRIC_DEFS = [
  { key: 'revenue',          label: 'Revenue (Cr)',         fmt: v => fmt(v, ' Cr', 0), higher: true  },
  { key: 'net_income',       label: 'Net Income (Cr)',      fmt: v => fmt(v, ' Cr', 0), higher: true  },
  { key: 'revenue_growth',   label: 'Revenue Growth',       fmt: pct,                   higher: true  },
  { key: 'profit_margin',    label: 'Profit Margin',        fmt: pct,                   higher: true  },
  { key: 'roe',              label: 'ROE',                  fmt: pct,                   higher: true  },
  { key: 'cas',              label: 'CAS (Alpha Score)',    fmt: v => fmt(v, '', 2),    higher: true  },
  { key: 'momentum',         label: 'Momentum Alpha',       fmt: v => fmt(v, '', 2),    higher: true  },
  { key: 'quality',          label: 'Quality Alpha',        fmt: v => fmt(v, '', 2),    higher: true  },
  { key: 'risk_score',       label: 'Risk Score (↓ better)',fmt: v => fmt(v, '/100', 0),higher: false },
  { key: 'volatility',       label: 'Annual Volatility',    fmt: pct,                   higher: false },
  { key: 'rsi',              label: 'RSI',                  fmt: v => fmt(v, '', 1),    higher: null  },
]

function MetricsTable({ metrics, idA, idB }) {
  const available = METRIC_DEFS.filter(m => metrics[m.key] && (metrics[m.key][idA] != null || metrics[m.key][idB] != null))

  return (
    <div>
      <p className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-wider mb-3">
        Side-by-Side Metrics — <span className="text-green-400">Best value highlighted</span>
      </p>
      <div className="elevated rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-erebus-surface border-b border-white/[0.07]">
              <th className="px-5 py-3 text-left text-[10px] font-mono text-erebus-text-3 uppercase tracking-wider w-44">Metric</th>
              {[idA, idB].map((id, i) => (
                <th key={id} className="px-5 py-3 text-left">
                  <p className="text-[11px] font-mono font-semibold" style={{ color: PALETTE[i] }}>{id}</p>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {available.map((m, mi) => {
              const va = metrics[m.key]?.[idA]
              const vb = metrics[m.key]?.[idB]
              let bestIsA = false, bestIsB = false
              if (m.higher !== null && va != null && vb != null) {
                bestIsA = m.higher ? va >= vb : va <= vb
                bestIsB = !bestIsA
              }
              return (
                <tr key={m.key} className={`border-t border-white/[0.05] ${mi % 2 === 1 ? 'bg-white/[0.01]' : ''}`}>
                  <td className="px-5 py-3 text-[12px] text-erebus-text-2 font-medium">{m.label}</td>
                  {[{v: va, best: bestIsA}, {v: vb, best: bestIsB}].map(({v, best}, ci) => (
                    <td key={ci} className="px-5 py-3">
                      <div className="flex items-center gap-1.5">
                        <span className={`text-[13px] font-mono ${best ? 'font-semibold text-green-400' : 'text-erebus-text-2'}`}>
                          {m.fmt(v)}
                        </span>
                        {best && v != null && (m.higher ? <TrendingUp size={11} className="text-green-400 shrink-0" /> : <TrendingDown size={11} className="text-green-400 shrink-0" />)}
                      </div>
                    </td>
                  ))}
                </tr>
              )
            })}
            {available.length === 0 && (
              <tr><td colSpan={3} className="px-5 py-6 text-center text-[12px] text-erebus-text-3">No metrics available for this comparison.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/* ── Key differences ─────────────────────────────────────────────── */
function KeyDiffs({ diffs }) {
  if (!diffs?.length) return null
  return (
    <div className="elevated rounded-xl p-5 space-y-2">
      <p className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-wider mb-3">Key Differences</p>
      {diffs.map((d, i) => (
        <div key={i} className="flex items-start gap-2.5">
          <div className="w-1 h-1 rounded-full bg-erebus-gold mt-2 shrink-0" />
          <p className="text-[13px] text-erebus-text-1 leading-relaxed">{d}</p>
        </div>
      ))}
    </div>
  )
}

/* ── AI Explanation ──────────────────────────────────────────────── */
function Explanation({ text, loading }) {
  if (loading) return (
    <div className="elevated rounded-xl p-6 flex items-center gap-3">
      <Loader2 size={14} className="text-erebus-gold animate-spin" />
      <p className="text-[13px] text-erebus-text-3">Generating AI analysis…</p>
    </div>
  )
  if (!text) return null
  return (
    <div className="elevated rounded-xl p-6">
      <p className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-wider mb-3">AI Narrative (Groq)</p>
      <p className="text-[14px] text-erebus-text-1 leading-[1.8] whitespace-pre-wrap">{text}</p>
      <p className="text-[11px] font-mono text-erebus-text-3 mt-3">
        Generated by EREBUS · Not investment advice
      </p>
    </div>
  )
}

/* ── Locked preview (skeleton) ───────────────────────────────────── */
function LockedPreview({ count }) {
  return (
    <div className="relative mt-8 overflow-hidden rounded-2xl">
      <div className="absolute inset-0 z-10 flex flex-col items-center justify-center backdrop-blur-sm bg-erebus-bg/70 rounded-2xl">
        <GitCompare size={20} className="text-erebus-text-3 mb-3" />
        <p className="text-[14px] font-medium text-erebus-text-2 mb-1">
          {count === 0 ? 'Add 2 companies to compare' : 'Add one more company to unlock analysis'}
        </p>
        <p className="text-[12px] font-mono text-erebus-text-3">Radar · Scores · Metrics · AI Insight</p>
      </div>
      <div className="pointer-events-none select-none blur-[2px]">
        <div className="elevated rounded-xl p-6 mb-4">
          <div className="h-3 bg-white/[0.05] rounded w-32 mb-6" />
          <div className="h-52 bg-white/[0.03] rounded-lg flex items-center justify-center">
            <div className="w-36 h-36 rounded-full border border-white/[0.07]" />
          </div>
        </div>
        <div className="elevated rounded-xl overflow-hidden">
          {[0,1,2,3,4].map(i => (
            <div key={i} className="flex gap-8 px-5 py-3 border-b border-white/[0.05]">
              <div className="h-2.5 bg-white/[0.07] rounded w-32" />
              <div className="h-2.5 bg-white/[0.05] rounded flex-1" />
              <div className="h-2.5 bg-white/[0.05] rounded flex-1" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

/* ── Main page ───────────────────────────────────────────────────── */
export default function ComparePage() {
  const [selected,        setSelected]        = useState([])
  const [loading,         setLoading]         = useState(false)
  const [result,          setResult]          = useState(null)
  const [error,           setError]           = useState(null)
  const [deepMode,        setDeepMode]        = useState(false)
  // S3 company universe
  const [universe,        setUniverse]        = useState([])
  const [universeLoading, setUniverseLoading] = useState(true)
  const [universeError,   setUniverseError]   = useState(null)

  // S3 source documents
  const [s3Files,    setS3Files]    = useState([])
  const [s3Loading,  setS3Loading]  = useState(true)
  const [viewerUrl,  setViewerUrl]  = useState(null)
  const [viewerName, setViewerName] = useState('')

  async function openFile(fileKey, name) {
    try {
      const url = await generateDownloadUrl(fileKey)
      setViewerName(name || fileKey.split('/').pop())
      setViewerUrl(url)
    } catch (e) { alert(`Could not open: ${e.message || e}`) }
  }

  const MAX = 2
  const canCompare = selected.length === 2

  // Load S3 company list on mount + re-fetch when tab regains focus
  function loadUniverse(opts = {}) {
    const { silent = false } = opts
    if (!silent) setUniverseLoading(true)
    setUniverseError(null)
    fetchCompanies()
      .then(data => {
        setUniverse(data.companies || [])
        setUniverseError(null)
      })
      .catch(err => {
        setUniverseError(typeof err === 'string' ? err : 'Failed to load company list')
        setUniverse([])
      })
      .finally(() => setUniverseLoading(false))
  }

  useEffect(() => {
    loadUniverse()
    const onFocus = () => loadUniverse({ silent: true })
    window.addEventListener('focus', onFocus)
    return () => window.removeEventListener('focus', onFocus)
  }, [])

  useEffect(() => {
    setS3Loading(true)
    listS3Files({ maxKeys: 100 })
      .then(files => setS3Files(files))
      .catch(e => console.warn('[ComparePage] S3 files:', e))
      .finally(() => setS3Loading(false))
  }, [])

  function handleRefreshUniverse() { loadUniverse() }

  function handleAdd(ticker) {
    const norm = ticker.trim().toUpperCase()
    if (selected.length < MAX && !selected.includes(norm)) {
      setSelected(prev => [...prev, norm])
      setResult(null)
      setError(null)
    }
  }

  function handleRemove(ticker) {
    setSelected(prev => prev.filter(t => t !== ticker))
    setResult(null)
    setError(null)
  }

  async function handleCompare() {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await compareCompanies(selected[0], selected[1], deepMode ? 'deep' : 'normal')
      setResult(data)
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Comparison failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const idA = selected[0]
  const idB = selected[1]

  return (
    <div className="flex-1 overflow-y-auto scrollbar-none bg-erebus-bg">
      <div className="max-w-4xl mx-auto px-6 pt-8 pb-20">

        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <GitCompare size={18} className="text-erebus-gold" />
            <h1 className="font-serif text-[26px] text-erebus-text-1">Compare</h1>
          </div>
          <p className="text-[13px] font-mono text-erebus-text-3">
            Select 2 companies from S3 for a live multi-dimensional intelligence comparison
          </p>
        </div>

        {/* S3 universe status bar */}
        <div className="flex items-center gap-3 mb-5">
          {universeLoading ? (
            <div className="flex items-center gap-2 text-[11px] font-mono text-erebus-text-3">
              <Loader2 size={11} className="animate-spin" /> Loading companies from S3…
            </div>
          ) : universeError ? (
            <div className="flex items-center gap-2 text-[11px] font-mono text-yellow-400/70">
              <AlertCircle size={11} /> {universeError} — type tickers manually
              <button onClick={handleRefreshUniverse} className="ml-1 hover:text-yellow-300 transition-colors">
                <RefreshCw size={11} />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-[11px] font-mono text-erebus-text-3">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              {universe.length} companies discovered in S3
              <button
                onClick={handleRefreshUniverse}
                className="ml-1 text-erebus-text-3 hover:text-erebus-text-2 transition-colors"
                title="Refresh company list"
              >
                <RefreshCw size={10} />
              </button>
            </div>
          )}
        </div>

        {/* Hint */}
        {!canCompare && !result && (
          <div className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-erebus-gold/[0.06] border border-erebus-gold/20 mb-6">
            <div className="w-1.5 h-1.5 rounded-full bg-erebus-gold animate-pulse shrink-0" />
            <p className="text-[13px] text-erebus-gold/80">
              {selected.length === 0
                ? 'Start by adding your first company — search by name or type any ticker'
                : 'Add one more company to unlock the comparison'}
            </p>
          </div>
        )}

        {/* Slots */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5">
          {selected.map((ticker, i) => (
            <FilledSlot key={ticker} ticker={ticker} index={i} onRemove={handleRemove} disabled={loading} />
          ))}
          {selected.length < MAX && Array.from({ length: MAX - selected.length }).map((_, i) => (
            <EmptySlot
              key={`e-${i}`}
              index={selected.length + i}
              onSelect={handleAdd}
              disabled={loading}
              universe={universe}
              loadingUniverse={universeLoading}
            />
          ))}
        </div>

        {/* Controls */}
        {canCompare && (
          <div className="flex items-center gap-3 mt-2 mb-1">
            <button
              onClick={handleCompare}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-[13px] font-semibold btn-gold disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading
                ? <><Loader2 size={14} className="animate-spin" /> Analysing…</>
                : <><GitCompare size={14} /> Compare<ArrowRight size={13} /></>
              }
            </button>
            <label className="flex items-center gap-2 text-[12px] font-mono text-erebus-text-3 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={deepMode}
                onChange={e => setDeepMode(e.target.checked)}
                className="accent-yellow-500"
              />
              Deep mode (AI narrative)
            </label>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="flex items-center gap-2.5 mt-4 px-4 py-3 rounded-xl bg-red-500/[0.06] border border-red-500/20">
            <AlertCircle size={14} className="text-red-400 shrink-0" />
            <p className="text-[13px] text-red-400">{error}</p>
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <div className="space-y-5 mt-8 animate-[fade-up_0.4s_ease_forwards]">
            <WinnerBanner
              summary={result.summary}
              confidence={result.confidence}
              idA={idA}
              idB={idB}
            />
            {/* Data quality warnings */}
            {result.warnings?.length > 0 && (
              <WarningsPanel warnings={result.warnings} />
            )}
            <KeyDiffs diffs={result.key_differences} />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <CompareRadar chartData={result.chart_data} idA={idA} idB={idB} />
              <ScoresChart  scores={result.scores}        idA={idA} idB={idB} />
            </div>
            <MetricsTable metrics={result.metrics} idA={idA} idB={idB} />
            <Explanation  text={result.explanation} loading={false} />
          </div>
        )}

        {/* Locked preview */}
        {!result && !loading && (
          <LockedPreview count={selected.length} />
        )}

        {/* ── Source Documents Panel ───────────────────────── */}
        <div className="mt-10">
          <p className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-wider mb-3 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-erebus-blue" />
            Source Documents — uploads &amp; ocr-uploads
          </p>
          {s3Loading ? (
            <div className="flex items-center gap-2 text-[12px] text-erebus-text-3 py-3">
              <Loader2 size={12} className="animate-spin" /> Loading files…
            </div>
          ) : s3Files.length === 0 ? (
            <p className="text-[12px] text-erebus-text-3 py-3">No uploaded files found.</p>
          ) : (
            <div className="elevated rounded-xl overflow-hidden">
              {s3Files.slice(0, 20).map((f, i) => {
                const name = f.name || f.file_key?.split('/').pop() || '—'
                const isOcr = f.file_key?.startsWith('ocr-uploads')
                return (
                  <button
                    key={f.file_key || i}
                    onClick={() => openFile(f.file_key, name)}
                    className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-erebus-surface-2 transition-colors text-left border-b border-white/[0.05] last:border-b-0"
                  >
                    <FileText size={13} className={isOcr ? 'text-erebus-gold' : 'text-erebus-blue'} />
                    <span className="flex-1 text-[12px] text-erebus-text-2 truncate">{name}</span>
                    <span className="text-[10px] font-mono text-erebus-text-3 shrink-0">
                      {isOcr ? 'OCR' : 'Upload'}
                    </span>
                    <ArrowRight size={11} className="text-erebus-text-3 shrink-0" />
                  </button>
                )
              })}
            </div>
          )}
        </div>
      </div>

      <FileViewer
        url={viewerUrl}
        fileName={viewerName}
        onClose={() => { setViewerUrl(null); setViewerName('') }}
      />
    </div>
  )
}
