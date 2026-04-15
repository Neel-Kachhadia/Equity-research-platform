// src/pages/app/ResearchPage.jsx
import { useState, useEffect, useCallback } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import {
  Search, X, FileText, TrendingUp, TrendingDown,
  AlertTriangle, ExternalLink, ChevronRight, ArrowLeft,
  Zap, Cpu, ChevronDown,
} from 'lucide-react'
import AnalyzeResults from '../../components/analyze/AnalyzeResults'
import { analyzeCompany } from '../../services/api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import EmptyState from '../../components/ui/EmptyState'
import SkeletonCard from '../../components/ui/SkeletonCard'
import { fetchDashboardSummary } from '../../services/api'

/* ── Universe and Mock data are removed to ensure we build exclusively from S3 db ────────────────── */

/* ── Custom tooltip ─────────────────────────────────────────────── */
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="elevated rounded-lg px-3 py-2 text-[12px]">
      <p className="text-erebus-text-3 font-mono">{label}</p>
      <p className="text-erebus-gold font-mono font-semibold">{payload[0].value}</p>
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════════════
   SearchPanel — shown when NO company is selected (search-first UX)
   Our change: clean search-first empty state with recents + trending.
═══════════════════════════════════════════════════════════════════ */
function SearchPanel({ onSelect }) {
  const [query, setQuery] = useState('')
  const [focused, setFocused] = useState(false)
  const [universe, setUniverse] = useState([])
  const [recents, setRecents] = useState([])
  const [trending, setTrending] = useState([])

  useEffect(() => {
    fetchDashboardSummary()
      .then(res => {
        const db = res.companies || []
        if (db.length > 0) {
          setUniverse(db.map(c => ({ ticker: c.ticker, name: c.ticker, sector: c.sector || 'Unclassified', score: c.score || 50 })))
          setRecents(db.slice(0, 4).map(c => c.ticker))
          const scoreSorted = [...db].sort((a, b) => (b.score || 0) - (a.score || 0))
          setTrending(scoreSorted.slice(0, 6).map(c => ({ ticker: c.ticker, sector: c.sector || 'Unclassified' })))
        }
      })
      .catch(err => console.log('Failed connecting Research db summary:', err))
  }, [])

  const matches = query.length > 0
    ? universe.filter(c =>
      c.ticker.toLowerCase().includes(query.toLowerCase()) ||
      c.name.toLowerCase().includes(query.toLowerCase()) ||
      c.sector.toLowerCase().includes(query.toLowerCase())
    )
    : []

  return (
    <div className="flex-1 flex items-center justify-center bg-erebus-bg px-6">
      <div className="w-full max-w-xl">
        <h1 className="font-serif text-[36px] text-erebus-text-1 text-center mb-2">
          Research Workspace
        </h1>
        <p className="text-[14px] text-erebus-text-3 text-center mb-8">
          Search any listed Indian company to begin analysis
        </p>

        {/* Search input */}
        <div
          className={`relative rounded-xl border transition-all duration-200 bg-erebus-surface
            ${focused
              ? 'border-erebus-gold/50 shadow-[0_0_0_3px_rgba(201,168,76,0.08)]'
              : 'border-white/[0.10]'
            }`}
        >
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-erebus-text-3" />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setTimeout(() => setFocused(false), 150)}
            placeholder="Search company to research…"
            className="w-full bg-transparent pl-11 pr-11 py-4 text-[15px] text-erebus-text-1 outline-none"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-erebus-text-3 hover:text-erebus-text-2"
            >
              <X size={15} />
            </button>
          )}

          {/* Dropdown */}
          {focused && (
            <div className="absolute top-full mt-1.5 left-0 right-0 bg-erebus-surface-2 border border-white/[0.09] rounded-xl shadow-[0_8px_32px_rgba(0,0,0,0.5)] z-20 overflow-hidden">
              {matches.length > 0 ? (
                matches.map(c => (
                  <button
                    key={c.ticker}
                    onMouseDown={() => onSelect(c.ticker)}
                    className="w-full flex items-center justify-between gap-3 px-4 py-3 hover:bg-white/[0.04] transition-colors text-left"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="ticker text-erebus-gold text-[13px]">{c.ticker}</span>
                        <span className="text-[11px] text-erebus-text-3 font-mono">{c.sector}</span>
                      </div>
                      <p className="text-[13px] text-erebus-text-2 mt-0.5">{c.name}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-[14px] font-mono font-semibold text-erebus-text-1">{c.score}</p>
                      <p className="text-[10px] font-mono text-erebus-text-3">Score</p>
                    </div>
                  </button>
                ))
              ) : query ? (
                <div className="px-4 py-6 text-center">
                  <p className="text-[13px] text-erebus-text-3">No company found for "{query}"</p>
                  <p className="text-[11px] text-erebus-text-3 mt-1">Try a different name, ticker, or sector</p>
                </div>
              ) : null}
            </div>
          )}
        </div>

        {/* Recent searches */}
        <div className="mt-6">
          <p className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-wider mb-3">Recent</p>
          <div className="flex flex-wrap gap-2">
            {recents.map(t => (
              <button
                key={t}
                onClick={() => onSelect(t)}
                className="px-3 py-1.5 rounded-lg text-[12px] font-mono text-erebus-text-2 bg-erebus-surface border border-white/[0.07] hover:border-erebus-gold/30 hover:text-erebus-gold transition-all duration-150"
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* Suggested / trending */}
        <div className="mt-8">
          <p className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-wider mb-3">
            Trending this week (Live S3)
          </p>
          <div className="grid grid-cols-3 gap-3">
            {trending.map(c => (
              <button
                key={c.ticker}
                onClick={() => onSelect(c.ticker)}
                className="elevated rounded-xl px-3 py-2.5 text-left hover:border-erebus-gold/25 transition-all duration-150 card-interactive"
              >
                <p className="ticker text-erebus-gold text-[12px]">{c.ticker}</p>
                <p className="text-[11px] text-erebus-text-3 mt-0.5 truncate">{c.sector}</p>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════════════
   LockedAnalyzePanel — analyse controls locked to the current ticker.
   No company search input — the ticker comes from the URL / prop.
═══════════════════════════════════════════════════════════════════ */
const ANALYZE_MODES = [
  { id: 'normal', label: 'Normal', Icon: Zap, desc: 'Fast structured output — ranking, quant, alpha. No LLM.' },
  { id: 'deep', label: 'Deep', Icon: Cpu, desc: 'Normal + RAG retrieval + LLM narrative. ~20–30 s.' },
]
const LLM_PROVIDERS = ['gemini', 'openai', 'anthropic', 'ollama']

function LockedAnalyzePanel({ ticker, onSubmit, loading }) {
  const [mode, setMode] = useState('normal')
  const [llmProvider, setLlmProvider] = useState('gemini')

  function handleSubmit(e) {
    e.preventDefault()
    onSubmit(ticker, mode, llmProvider)
  }

  return (
    <form onSubmit={handleSubmit} className="elevated rounded-xl p-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="section-label">EREBUS Analyze</span>
          <div className="chip-gold text-[10px] font-mono px-2 py-0.5 rounded-full">/analyze API</div>
        </div>
        {/* Locked company badge */}
        <div
          className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-[12px] font-mono"
          style={{ background: 'rgba(201,168,76,0.08)', border: '1px solid rgba(201,168,76,0.25)', color: '#C9A84C' }}
        >
          {ticker}
          <span className="text-[10px] opacity-60">locked</span>
        </div>
      </div>

      {/* Mode toggle */}
      <div className="space-y-2">
        <p className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-widest">Analysis Mode</p>
        <div className="grid grid-cols-2 gap-2">
          {ANALYZE_MODES.map(({ id, label, Icon, desc }) => {
            const active = mode === id
            return (
              <button
                key={id}
                type="button"
                disabled={loading}
                onClick={() => setMode(id)}
                className={[
                  'flex flex-col items-start gap-1 p-3 rounded-lg text-left border transition-all duration-200',
                  'disabled:opacity-40 disabled:cursor-not-allowed',
                  active
                    ? 'border-erebus-gold/40 bg-[rgba(201,168,76,0.07)]'
                    : 'border-white/[0.08] hover:border-white/[0.16] bg-erebus-bg',
                ].join(' ')}
              >
                <div className="flex items-center gap-1.5">
                  <Icon size={12} className={active ? 'text-erebus-gold' : 'text-erebus-text-3'} />
                  <span className={`text-[12px] font-mono font-medium ${active ? 'text-erebus-gold' : 'text-erebus-text-2'}`}>
                    {label}
                  </span>
                </div>
                <p className="text-[10px] text-erebus-text-3 leading-relaxed">{desc}</p>
              </button>
            )
          })}
        </div>
      </div>

      {/* LLM Provider — deep mode only */}
      {mode === 'deep' && (
        <div className="space-y-1.5">
          <label htmlFor="llm-provider-select" className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-widest">
            LLM Provider
          </label>
          <div className="relative">
            <select
              id="llm-provider-select"
              value={llmProvider}
              onChange={e => setLlmProvider(e.target.value)}
              disabled={loading}
              className="input-erebus w-full appearance-none bg-erebus-bg text-erebus-text-1 text-[13px] font-mono px-4 py-2.5 rounded-lg border border-white/[0.08] cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {LLM_PROVIDERS.map(p => (
                <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
              ))}
            </select>
            <ChevronDown size={13} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-erebus-text-3 pointer-events-none" />
          </div>
        </div>
      )}

      {/* Submit */}
      <button
        type="submit"
        disabled={loading}
        className="btn-gold w-full py-2.5 rounded-lg text-[13px] font-semibold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? (
          <>
            <span className="inline-block w-3.5 h-3.5 rounded-full border-2 border-erebus-bg/30 border-t-erebus-bg animate-spin" />
            Analyzing…
          </>
        ) : (
          `Analyse ${ticker} →`
        )}
      </button>
    </form>
  )
}

/* ═══════════════════════════════════════════════════════════════════
   CompanyCockpit — shown when a company IS selected
   Merges:
   - Our change  : cockpit layout (metrics, filings, peers, risks, quick-ask)
   - Teammates's : AnalyzePanel + AnalyzeResults integration at the top
═══════════════════════════════════════════════════════════════════ */
function CompanyCockpit({ ticker, onClear }) {
  const [loading, setLoading] = useState(true)

  // ── Teammate's: /analyze API integration ──────────────────────────
  const [analyzeStatus, setAnalyzeStatus] = useState('idle')   // idle | loading | success | error
  const [analyzeResponse, setAnalyzeResponse] = useState(null)
  const [analyzeError, setAnalyzeError] = useState(null)
  const [analyzeMode, setAnalyzeMode] = useState('normal')

  /**
   * Called by <AnalyzePanel onSubmit={...} />
   * Manages the full request lifecycle.
   */
  const handleAnalyze = useCallback(async (companyId, mode, llmProvider) => {
    setAnalyzeMode(mode)
    setAnalyzeStatus('loading')
    setAnalyzeResponse(null)
    setAnalyzeError(null)

    try {
      const data = await analyzeCompany(companyId, mode, llmProvider)
      setAnalyzeResponse(data)
      setAnalyzeStatus('success')
    } catch (err) {
      // err is already a human-readable string from api.js
      setAnalyzeError(typeof err === 'string' ? err : 'Something went wrong.')
      setAnalyzeStatus('error')
    }
  }, [])

  /** Retry — resets to idle so user can re-submit the panel */
  const handleRetry = useCallback(() => {
    setAnalyzeStatus('idle')
    setAnalyzeError(null)
    setAnalyzeResponse(null)
  }, [])

  // Reset results whenever the user navigates to a different company
  useEffect(() => {
    setAnalyzeStatus('idle')
    setAnalyzeResponse(null)
    setAnalyzeError(null)
  }, [ticker])

  // ── Our original: skeleton loader ─────────────────────────────────
  useEffect(() => {
    setLoading(true)
    const t = setTimeout(() => setLoading(false), 800)
    return () => clearTimeout(t)
  }, [ticker])

  if (loading) {
    return (
      <div className="flex-1 overflow-y-auto bg-erebus-bg px-6 py-6">
        <div className="max-w-4xl mx-auto space-y-4">
          <SkeletonCard height="h-24" />
          <div className="grid grid-cols-4 gap-3">
            {[0, 1, 2, 3].map(i => <SkeletonCard key={i} lines={2} />)}
          </div>
          <SkeletonCard lines={4} />
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto bg-erebus-bg scrollbar-none">

      {/* Breadcrumb toolbar */}
      <div className="sticky top-0 z-10 bg-erebus-bg/90 backdrop-blur-md border-b border-white/[0.06] px-6 py-3 flex items-center gap-3">
        <button
          onClick={onClear}
          className="text-erebus-text-3 hover:text-erebus-gold transition-colors flex items-center gap-1 text-[12px] font-mono"
        >
          <ArrowLeft size={12} /> Research
        </button>
        <ChevronRight size={11} className="text-erebus-text-3" />
        <span className="ticker text-erebus-gold text-[13px]">{ticker}</span>
        <span className="text-[12px] text-erebus-text-3">Company Cockpit</span>
      </div>

      <div className="px-6 py-6 max-w-4xl mx-auto">

        {/* ── Locked Analyze Panel — always uses the current ticker ──── */}
        <LockedAnalyzePanel
          ticker={ticker}
          onSubmit={handleAnalyze}
          loading={analyzeStatus === 'loading'}
        />
        <AnalyzeResults
          status={analyzeStatus}
          response={analyzeResponse}
          error={analyzeError}
          mode={analyzeMode}
          onRetry={handleRetry}
        />









        {/* ── Our original: Quick ask ──────────────────────────────────── */}
        <div className="mt-5 elevated rounded-xl p-4">
          <div className="flex items-center gap-3">
            <input
              placeholder={`Ask anything about ${ticker}…`}
              className="input-erebus flex-1 bg-transparent text-[14px] text-erebus-text-1 outline-none"
            />
            <button className="px-4 py-2 text-[12px] font-semibold rounded-lg btn-gold shrink-0">Ask</button>
          </div>
          <p className="text-[11px] font-mono text-erebus-text-3 mt-2">
            Opens full Chat workspace with {ticker} context pre-loaded
          </p>
        </div>

      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════════════
   ResearchPage — our search-first routing (URL-driven)
═══════════════════════════════════════════════════════════════════ */
export default function ResearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const company = searchParams.get('company')

  function selectCompany(ticker) {
    setSearchParams({ company: ticker })
  }

  function clearCompany() {
    setSearchParams({})
  }

  if (!company) return <SearchPanel onSelect={selectCompany} />
  return <CompanyCockpit ticker={company} onClear={clearCompany} />
}
