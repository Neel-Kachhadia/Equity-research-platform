// src/components/analyze/AnalyzePanel.jsx
//
// Fix #6 — Fully decoupled from AnalyzeResults.
// Owns only inputs + validation. Reports up via onSubmit callback.
//
import { useState } from 'react'
import { Search, ChevronDown, Zap, Cpu } from 'lucide-react'

const MODES = [
  {
    id: 'normal',
    label: 'Normal',
    icon: Zap,
    desc: 'Fast structured output — ranking, quant, alpha signals. No LLM.',
  },
  {
    id: 'deep',
    label: 'Deep',
    icon: Cpu,
    desc: 'All of Normal + RAG document retrieval + LLM narrative. ~20–30 s.',
  },
]

const LLM_PROVIDERS = ['gemini', 'openai', 'anthropic', 'ollama']

/**
 * AnalyzePanel
 *
 * Props:
 *   onSubmit(companyId, mode, llmProvider) → void
 *   loading → bool   (controls disabled state)
 *   initialCompanyId → string  (pre-fills the ticker from URL)
 */
export default function AnalyzePanel({ onSubmit, loading, initialCompanyId = '' }) {
  const [companyId, setCompanyId]         = useState(initialCompanyId)
  const [mode, setMode]                   = useState('normal')
  const [llmProvider, setLlmProvider]     = useState('gemini')
  const [validationErr, setValidationErr] = useState('')

  function handleSubmit(e) {
    e.preventDefault()

    // ── Client-side validation ─────────────────────────────────────
    const trimmed = companyId.trim().toUpperCase()
    if (!trimmed) {
      setValidationErr('Company ID is required. Example: RELIANCE, TCS, HDFC')
      return
    }
    if (trimmed.length > 30) {
      setValidationErr('Company ID looks too long. Use the ticker symbol, e.g. TCS')
      return
    }
    setValidationErr('')

    onSubmit(trimmed, mode, llmProvider)
  }

  return (
    <form
      id="analyze-panel"
      onSubmit={handleSubmit}
      className="elevated rounded-xl p-6 space-y-5"
    >
      {/* ── Header ─────────────────────────────────────────────────── */}
      <div className="flex items-center gap-2">
        <span className="section-label">EREBUS Analyze</span>
        <div className="chip-gold text-[10px] font-mono px-2 py-0.5 rounded-full">
          /analyze API
        </div>
      </div>

      {/* ── Company ID input ───────────────────────────────────────── */}
      <div className="space-y-1.5">
        <label
          htmlFor="company-id-input"
          className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-widest"
        >
          Company Ticker / ID
        </label>
        <div className="relative">
          <Search
            size={14}
            className="absolute left-3.5 top-1/2 -translate-y-1/2 text-erebus-text-3 pointer-events-none"
          />
          <input
            id="company-id-input"
            type="text"
            value={companyId}
            onChange={e => {
              setCompanyId(e.target.value)
              setValidationErr('')
            }}
            placeholder="e.g. RELIANCE, TCS, HDFCBANK"
            disabled={loading}
            className="input-erebus w-full bg-erebus-bg text-erebus-text-1 text-[13px]
                       pl-9 pr-4 py-2.5 rounded-lg border border-white/[0.08]
                       disabled:opacity-40 disabled:cursor-not-allowed"
          />
        </div>
        {validationErr && (
          <p className="text-[11px] font-mono text-erebus-red mt-1">{validationErr}</p>
        )}
      </div>

      {/* ── Mode toggle ────────────────────────────────────────────── */}
      <div className="space-y-2">
        <p className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-widest">
          Analysis Mode
        </p>
        <div className="grid grid-cols-2 gap-2">
          {MODES.map(({ id, label, icon: Icon, desc }) => {
            const active = mode === id
            return (
              <button
                key={id}
                type="button"
                id={`mode-${id}`}
                disabled={loading}
                onClick={() => setMode(id)}
                className={[
                  'flex flex-col items-start gap-1 p-3 rounded-lg text-left',
                  'border transition-all duration-200',
                  'disabled:opacity-40 disabled:cursor-not-allowed',
                  active
                    ? 'border-erebus-gold/40 bg-[rgba(201,168,76,0.07)]'
                    : 'border-white/[0.08] hover:border-white/[0.16] bg-erebus-bg',
                ].join(' ')}
              >
                <div className="flex items-center gap-1.5">
                  <Icon
                    size={12}
                    className={active ? 'text-erebus-gold' : 'text-erebus-text-3'}
                  />
                  <span
                    className={`text-[12px] font-mono font-medium ${
                      active ? 'text-erebus-gold' : 'text-erebus-text-2'
                    }`}
                  >
                    {label}
                  </span>
                </div>
                <p className="text-[10px] text-erebus-text-3 leading-relaxed">{desc}</p>
              </button>
            )
          })}
        </div>
      </div>

      {/* ── LLM Provider (deep mode only) — Fix #1 ────────────────── */}
      {mode === 'deep' && (
        <div className="space-y-1.5">
          <label
            htmlFor="llm-provider-select"
            className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-widest"
          >
            LLM Provider
          </label>
          <div className="relative">
            <select
              id="llm-provider-select"
              value={llmProvider}
              onChange={e => setLlmProvider(e.target.value)}
              disabled={loading}
              className="input-erebus w-full appearance-none bg-erebus-bg text-erebus-text-1
                         text-[13px] font-mono px-4 py-2.5 rounded-lg
                         border border-white/[0.08] cursor-pointer
                         disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {LLM_PROVIDERS.map(p => (
                <option key={p} value={p}>
                  {p.charAt(0).toUpperCase() + p.slice(1)}
                </option>
              ))}
            </select>
            <ChevronDown
              size={13}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-erebus-text-3 pointer-events-none"
            />
          </div>
        </div>
      )}

      {/* ── Submit ─────────────────────────────────────────────────── */}
      <button
        id="analyze-submit-btn"
        type="submit"
        disabled={loading}
        className="btn-gold w-full py-2.5 rounded-lg text-[13px] font-semibold
                   flex items-center justify-center gap-2
                   disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? (
          <>
            <span
              className="inline-block w-3.5 h-3.5 rounded-full border-2
                         border-erebus-bg/30 border-t-erebus-bg animate-spin"
            />
            Analyzing…
          </>
        ) : (
          'Run Analysis →'
        )}
      </button>
    </form>
  )
}
