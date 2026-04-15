import { useState, useRef, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Send, Paperclip, X, FileText, AlertCircle,
  Eye, BarChart3, MessageSquare, Sparkles, CheckCircle,
  TrendingUp, Shield, DollarSign, Activity, ExternalLink,
} from 'lucide-react'
import ModelSelector from '../../components/ui/ModelSelector'
import FileUploader from '../../components/ui/FileUploader'
import FileViewer from '../../components/ui/FileViewer'
import { chatWithErebus, generateDownloadUrl, createSession, updateSession, fetchSession } from '../../services/api'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Legend, Cell,
} from 'recharts'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function getPresignedUrl(fileKey) {
  const res = await fetch(`${API_BASE}/uploads/generate-download-url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_key: fileKey }),
  })
  if (!res.ok) throw new Error(`Could not get URL: ${res.status}`)
  const { download_url } = await res.json()
  return download_url
}

// ── Mock suggestion prompts ───────────────────────────────────────
const SUGGESTIONS = [
  { label: 'NIM trajectory', prompt: 'Analyse HDFC Bank\'s NIM trajectory over the last 6 quarters vs management guidance.' },
  { label: 'Guidance credibility', prompt: 'Rate Asian Paints management guidance credibility based on their last 4 earnings calls.' },
  { label: 'Peer ROE compare', prompt: 'Compare ROE of Titan Company vs Kalyan Jewellers across FY22–FY24.' },
  { label: 'Risk assessment', prompt: 'What are the top 3 risk factors for Infosys in the current macro environment?' },
]

// Model → LLM provider mapping (backend LLM_PROVIDER env overrides this anyway)
const PROVIDER_MAP = { quick: 'groq', deep: 'groq' }

// ── S3 Source Downloader ──────────────────────────────────────────
async function handleDownloadSource(s) {
  if (!s.file_key) return;
  try {
    const url = await generateDownloadUrl(s.file_key);
    if (url) window.open(url, '_blank');
  } catch (err) {
    console.error("Failed to generate download URL", err);
  }
}

// ── Lightweight markdown renderer ─────────────────────────────────
function renderMarkdown(text) {
  if (!text) return null
  return text.split('\n').map((line, i) => {
    const trimmed = line.trim()

    // Horizontal rule
    if (/^---+$/.test(trimmed) || /^===+$/.test(trimmed))
      return <hr key={i} className="border-white/10 my-3" />

    // Heading H3 / H2 / H1
    if (trimmed.startsWith('### '))
      return <p key={i} className="block font-semibold text-[13px] text-erebus-gold mt-3 mb-1">{trimmed.slice(4)}</p>
    if (trimmed.startsWith('## '))
      return <p key={i} className="block font-semibold text-[14px] text-erebus-gold mt-3 mb-1">{trimmed.slice(3)}</p>

    // Monospace table / financial data lines (contain | or purely dashes)
    if (trimmed.includes('|') || /^[-─]+$/.test(trimmed))
      return <span key={i} className="block font-mono text-[12px] text-erebus-text-2 leading-snug">{line}</span>

    // Bullet list  - item  or  * item
    if (/^[-*•]\s+/.test(trimmed))
      return (
        <span key={i} className="flex gap-2 items-start mt-1">
          <span className="text-erebus-gold mt-[3px] shrink-0">·</span>
          <span>{inlineMarkdown(trimmed.replace(/^[-*•]\s+/, ''))}</span>
        </span>
      )

    // Numbered list  1. item
    if (/^\d+\.\s+/.test(trimmed)) {
      const [num, ...rest] = trimmed.split(/\.\s+/, 2)
      return (
        <span key={i} className="flex gap-2 items-start mt-1">
          <span className="text-erebus-gold font-mono text-[11px] mt-[3px] shrink-0 w-4 text-right">{num}.</span>
          <span>{inlineMarkdown(rest.join('. '))}</span>
        </span>
      )
    }

    // Blank line
    if (trimmed === '') return <br key={i} />

    // Regular paragraph line
    return <span key={i} className="block">{inlineMarkdown(line)}</span>
  })
}

function inlineMarkdown(line) {
  return line.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/).map((part, j) => {
    if (part.startsWith('**') && part.endsWith('**'))
      return <strong key={j} className="text-erebus-text-1 font-semibold">{part.slice(2, -2)}</strong>
    if (part.startsWith('*') && part.endsWith('*'))
      return <em key={j} className="text-erebus-text-2">{part.slice(1, -1)}</em>
    return part
  })
}


// ── Custom Recharts Tooltip ────────────────────────────────────────
function ChartTooltip({ active, payload, label, suffix = '' }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg px-3 py-2 text-[12px] min-w-[140px]" style={{ background: '#0D1017', border: '1px solid rgba(255,255,255,0.10)', boxShadow: '0 8px 32px rgba(0,0,0,0.5)' }}>
      <p className="text-erebus-text-3 font-mono mb-1.5 border-b border-white/5 pb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="font-mono flex justify-between gap-3" style={{ color: p.color }}>
          <span className="opacity-70">{p.name}</span>
          <strong>{typeof p.value === 'number' ? p.value.toLocaleString('en-IN') : p.value}{suffix}</strong>
        </p>
      ))}
    </div>
  )
}

// ── Ratio Card ────────────────────────────────────────────────────
function RatioCard({ label, value, unit = '', icon: Icon, color = '#4A8FE7', sub }) {
  if (value == null) return null
  return (
    <div className="rounded-xl p-3 flex flex-col gap-1" style={{ background: `${color}0D`, border: `1px solid ${color}28` }}>
      <div className="flex items-center gap-1.5">
        <Icon size={11} style={{ color }} />
        <span className="text-[10px] font-mono uppercase tracking-wider text-erebus-text-3">{label}</span>
      </div>
      <p className="text-[20px] font-mono font-semibold leading-none mt-0.5" style={{ color }}>
        {typeof value === 'number' ? value.toLocaleString('en-IN', { maximumFractionDigits: 1 }) : value}
        <span className="text-[11px] ml-0.5 opacity-60">{unit}</span>
      </p>
      {sub && <span className="text-[9px] font-mono uppercase tracking-wider" style={{ color, opacity: 0.55 }}>{sub}</span>}
    </div>
  )
}

// ── Chart Panel (Data Tab) ────────────────────────────────────────
function ChartPanel({ chartData }) {
  if (!chartData) return (
    <div className="flex flex-col items-center justify-center py-12 gap-3">
      <BarChart3 size={32} className="text-erebus-text-3 opacity-25" />
      <p className="text-[12px] font-mono text-erebus-text-3 text-center max-w-xs">
        Ask about a specific company (e.g. "Infosys financials") to see live charts here.
      </p>
    </div>
  )

  const { company_id, sector, revenue = [], margins = [], ratios = {} } = chartData
  const hasRevenue = revenue.length > 0
  const hasMargins = margins.length > 0 && margins.some(m => m.net != null || m.ebit != null || m.gm != null)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <span className="ticker text-erebus-gold text-[16px] font-semibold">{company_id}</span>
          {sector && <span className="ml-2 text-[10px] font-mono text-erebus-text-3 uppercase tracking-wider">{sector}</span>}
        </div>
        <span className="chip-green text-[10px] font-mono px-2.5 py-1 rounded-full">● Live S3
        </span>
      </div>

      {/* Key ratio cards — colour-coded by threshold */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        <RatioCard
          label="Revenue" unit="" icon={DollarSign} color="#4A8FE7"
          value={ratios.revenue_cr != null ? `₹${(ratios.revenue_cr / 1000).toFixed(1)}k` : null}
          sub="INR Crore"
        />
        <RatioCard
          label="Net Margin" value={ratios.net_margin} unit="%" icon={TrendingUp}
          color={ratios.net_margin > 15 ? '#2ECC8A' : ratios.net_margin > 8 ? '#C9A84C' : '#D95555'}
          sub={ratios.net_margin > 15 ? 'Strong' : ratios.net_margin > 8 ? 'Moderate' : 'Thin'}
        />
        <RatioCard
          label="EBIT Margin" value={ratios.ebit_margin} unit="%" icon={Activity}
          color={ratios.ebit_margin > 20 ? '#2ECC8A' : ratios.ebit_margin > 10 ? '#C9A84C' : '#D95555'}
          sub={ratios.ebit_margin > 20 ? 'Healthy' : ratios.ebit_margin > 10 ? 'Average' : 'Weak'}
        />
        <RatioCard
          label="ROE" value={ratios.roe} unit="%" icon={TrendingUp}
          color={ratios.roe > 20 ? '#2ECC8A' : ratios.roe > 10 ? '#C9A84C' : '#D95555'}
          sub={ratios.roe > 20 ? 'Excellent' : ratios.roe > 10 ? 'Adequate' : 'Low'}
        />
        <RatioCard
          label="Gross Margin" value={ratios.gross_margin} unit="%" icon={Activity}
          color={ratios.gross_margin > 40 ? '#2ECC8A' : '#E09A25'}
        />
        <RatioCard
          label="Debt / Equity" value={ratios.de} unit="×" icon={Shield}
          color={ratios.de < 0.5 ? '#2ECC8A' : ratios.de < 1.5 ? '#C9A84C' : '#D95555'}
          sub={ratios.de < 0.5 ? 'Low leverage' : ratios.de < 1.5 ? 'Moderate' : 'High risk'}
        />
      </div>

      {/* D/E leverage gauge */}
      {ratios.de != null && (
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <p className="text-[10px] font-mono text-erebus-text-3 uppercase tracking-wider">Leverage Gauge</p>
            <span className="text-[11px] font-mono font-semibold" style={{
              color: ratios.de < 0.5 ? '#2ECC8A' : ratios.de < 1.5 ? '#C9A84C' : '#D95555'
            }}>{ratios.de}× D/E</span>
          </div>
          <div className="h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.05)' }}>
            <div className="h-full rounded-full transition-all duration-700" style={{
              width: `${Math.min(ratios.de / 3 * 100, 100)}%`,
              background: ratios.de < 0.5
                ? '#2ECC8A'
                : ratios.de < 1.5
                  ? 'linear-gradient(90deg,#C9A84C,#E09A25)'
                  : 'linear-gradient(90deg,#D95555,#FF4444)',
              boxShadow: `0 0 8px ${ratios.de < 0.5 ? '#2ECC8A55' : ratios.de < 1.5 ? '#C9A84C55' : '#D9555555'}`,
            }} />
          </div>
          <div className="flex justify-between mt-1">
            {['0×', '0.5×', '1×', '1.5×', '2×', '3×+'].map(v => (
              <span key={v} className="text-[9px] font-mono text-erebus-text-3">{v}</span>
            ))}
          </div>
        </div>
      )}

      {/* Revenue + Net Income + EBIT grouped combo bar */}
      {hasRevenue && (
        <div>
          <p className="text-[10px] font-mono text-erebus-text-3 uppercase tracking-wider mb-3">
            Revenue · Net Income · EBIT (INR Cr)
          </p>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={revenue} margin={{ top: 4, right: 4, left: 0, bottom: 0 }} barCategoryGap="28%" barGap={3}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
              <XAxis dataKey="year" tick={{ fill: '#4E5262', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#4E5262', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} tickFormatter={v => `${(v / 1000).toFixed(0)}k`} />
              <Tooltip content={<ChartTooltip suffix=" Cr" />} />
              <Legend wrapperStyle={{ fontSize: 10, fontFamily: 'JetBrains Mono', color: '#8A8D9A', paddingTop: 10 }} />
              <Bar dataKey="revenue" name="Revenue" fill="#4A8FE7" radius={[3, 3, 0, 0]} maxBarSize={26} isAnimationActive animationDuration={600} />
              <Bar dataKey="net_income" name="Net Income" fill="#2ECC8A" radius={[3, 3, 0, 0]} maxBarSize={26} isAnimationActive animationDuration={750} />
              <Bar dataKey="ebit" name="EBIT" fill="#C9A84C" radius={[3, 3, 0, 0]} maxBarSize={26} isAnimationActive animationDuration={900} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Margin trends — Net / EBIT / Gross margin lines */}
      {hasMargins && (
        <div>
          <p className="text-[10px] font-mono text-erebus-text-3 uppercase tracking-wider mb-3">Margin Trends (%)</p>
          <ResponsiveContainer width="100%" height={210}>
            <LineChart data={margins} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
              <XAxis dataKey="year" tick={{ fill: '#4E5262', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#4E5262', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} tickFormatter={v => `${v}%`} />
              <Tooltip content={<ChartTooltip suffix="%" />} />
              <Legend wrapperStyle={{ fontSize: 10, fontFamily: 'JetBrains Mono', color: '#8A8D9A', paddingTop: 6 }} />
              <Line type="monotone" dataKey="net" name="Net Margin" stroke="#2ECC8A" strokeWidth={2.5} dot={{ r: 4, fill: '#2ECC8A', strokeWidth: 0 }} activeDot={{ r: 6 }} connectNulls />
              <Line type="monotone" dataKey="ebit" name="EBIT Margin" stroke="#C9A84C" strokeWidth={2.5} dot={{ r: 4, fill: '#C9A84C', strokeWidth: 0 }} activeDot={{ r: 6 }} strokeDasharray="5 2" connectNulls />
              <Line type="monotone" dataKey="gm" name="Gross Margin" stroke="#4A8FE7" strokeWidth={2.5} dot={{ r: 4, fill: '#4A8FE7', strokeWidth: 0 }} activeDot={{ r: 6 }} strokeDasharray="2 4" connectNulls />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Interest coverage callout */}
      {ratios.interest_coverage != null && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.025)', border: '1px solid rgba(255,255,255,0.07)' }}>
          <Shield size={14} style={{ color: ratios.interest_coverage > 5 ? '#2ECC8A' : ratios.interest_coverage > 2 ? '#C9A84C' : '#D95555' }} className="shrink-0" />
          <span className="text-[12px] font-mono text-erebus-text-2">
            Interest Coverage{' '}
            <strong style={{ color: ratios.interest_coverage > 5 ? '#2ECC8A' : ratios.interest_coverage > 2 ? '#C9A84C' : '#D95555' }}>
              {ratios.interest_coverage}×
            </strong>
            <span className="text-erebus-text-3 ml-1.5">
              {ratios.interest_coverage > 5 ? '— comfortable debt service' : ratios.interest_coverage > 2 ? '— adequate coverage' : '— watch closely'}
            </span>
          </span>
        </div>
      )}

      {!hasRevenue && !hasMargins && (
        <p className="text-[12px] font-mono text-erebus-text-3 text-center py-6">
          Time-series data not available for this company in S3.
        </p>
      )}
    </div>
  )
}


// ── Source pill ────────────────────────────────────────────────────
function SourcePill({ source, onOpen, onSourcePanelClick }) {
  const canOpen = !!source.s3_key
  function handleClick() {
    if (canOpen) onOpen(source)
    else onSourcePanelClick()
  }
  return (
    <button
      onClick={handleClick}
      title={canOpen ? 'Open file' : 'View sources'}
      className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono chip-blue hover:opacity-80 transition-opacity"
    >
      <FileText size={10} />
      {source.label} · {source.page}
      {canOpen ? <Eye size={9} className="opacity-60" /> : <Eye size={9} className="opacity-40" />}
    </button>
  )
}

// ── Source card (Sources tab) ─────────────────────────────────────
function SourceCard({ source, onOpen }) {
  const [loading, setLoading] = useState(false)
  const canOpen = !!source.s3_key

  async function handleOpen() {
    if (!canOpen) return
    setLoading(true)
    try { await onOpen(source) } finally { setLoading(false) }
  }

  return (
    <div
      onClick={canOpen ? handleOpen : undefined}
      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg bg-erebus-bg border border-white/[0.07] ${canOpen ? 'cursor-pointer hover:border-erebus-gold/30 hover:bg-erebus-gold/[0.03] transition-colors group' : ''}`}
    >
      <FileText size={14} className="text-erebus-blue shrink-0" />
      <div className="flex-1 min-w-0">
        <p className={`text-[13px] font-medium text-erebus-text-1 ${canOpen ? 'group-hover:text-erebus-gold transition-colors' : ''}`}>{source.label}</p>
        <p className="text-[11px] font-mono text-erebus-text-3">{source.page}</p>
      </div>
      {canOpen && (
        loading
          ? <div className="w-3 h-3 rounded-full border border-erebus-gold/40 border-t-erebus-gold animate-spin" />
          : <Eye size={13} className="text-erebus-text-3 group-hover:text-erebus-gold transition-colors" />
      )}
    </div>
  )
}

// ── Message bubble ────────────────────────────────────────────────
function Message({ msg, onSourceClick, onOpenSource }) {
  const [activeTab, setActiveTab] = useState('answer')
  const tabs = [
    { id: 'answer', label: 'Answer', icon: MessageSquare },
    { id: 'sources', label: 'Sources', icon: FileText },
    { id: 'data', label: 'Data', icon: BarChart3 },
  ]

  if (msg.role === 'error') {
    return (
      <div className="flex gap-3 mb-5 items-start">
        <div className="w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5"
          style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)' }}>
          <AlertCircle size={12} className="text-red-400" />
        </div>
        <div className="flex-1 px-4 py-3 rounded-xl text-[13px] text-red-400 leading-relaxed"
          style={{ background: 'rgba(239,68,68,0.07)', border: '1px solid rgba(239,68,68,0.15)' }}>
          {msg.text}
        </div>
      </div>
    )
  }

  if (msg.role === 'user') {

    return (
      <div className="flex justify-end mb-5">
        <div className="max-w-lg px-4 py-3 rounded-xl rounded-tr-sm text-[14px] text-erebus-text-1 leading-relaxed bg-erebus-surface-2 border border-white/[0.07]">
          {msg.text}
        </div>
      </div>
    )
  }

  return (
    <div className="mb-6 max-w-2xl">
      {/* EREBUS mark + confidence badge */}
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        <div className="w-6 h-6 rounded-full flex items-center justify-center border border-erebus-gold/50 font-serif text-erebus-gold text-xs bg-erebus-gold/[0.08]">
          E
        </div>
        <span className="text-[11px] font-mono text-erebus-text-3">EREBUS · AI Research</span>
        {msg.context_loaded && (
          <span className="chip-green px-2 py-0.5 rounded text-[10px] font-mono">
            ● Live data · {msg.company_id}
          </span>
        )}
        {msg.model_used && (
          <span className="text-[10px] font-mono text-erebus-text-3 ml-1">
            via {msg.model_used}
          </span>
        )}
        {/* Confidence badge — only shown on successful pipeline runs */}
        {msg.confidence != null && !msg.failed_at && (
          <span
            className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold border"
            style={{
              color: msg.confidence >= 0.8 ? '#2ECC8A' : msg.confidence >= 0.6 ? '#C9A84C' : '#D95555',
              borderColor: msg.confidence >= 0.8 ? '#2ECC8A44' : msg.confidence >= 0.6 ? '#C9A84C44' : '#D9555544',
              background: msg.confidence >= 0.8 ? '#2ECC8A0D' : msg.confidence >= 0.6 ? '#C9A84C0D' : '#D955550D',
            }}
          >
            ✓ {Math.round(msg.confidence * 100)}% verified
          </span>
        )}
        {/* Gate failure warning — shown when pipeline was blocked */}
        {msg.failed_at && (
          <span
            className="px-2 py-0.5 rounded-full text-[10px] font-mono border"
            style={{ color: '#E09A25', borderColor: '#E09A2544', background: '#E09A250D' }}
            title={`Pipeline stopped at: ${msg.failed_at}`}
          >
            ⚠ {msg.failed_at.replace(/_/g, ' ')}
          </span>
        )}
      </div>

      {/* Tabs — always shown for assistant messages */}
      <div className="flex items-center gap-1 mb-4">
        {tabs.map(tab => {
          const Icon = tab.icon
          const hasData = tab.id === 'data' && (msg.chart_data != null)
          const hasSrc = tab.id === 'sources' && msg.sources?.length > 0
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[12px] font-medium
                transition-all duration-150
                ${activeTab === tab.id
                  ? 'bg-erebus-surface-2 text-erebus-text-1 border border-white/[0.08]'
                  : 'text-erebus-text-3 hover:text-erebus-text-2'
                }
              `}
            >
              <Icon size={12} />
              {tab.label}
              {(hasData || hasSrc) && (
                <span className="w-1.5 h-1.5 rounded-full bg-erebus-gold ml-0.5" />
              )}
            </button>
          )
        })}
      </div>

      {/* Content area */}
      <div className="elevated rounded-xl p-5">
        {activeTab === 'answer' && (
          <>
            <div className="text-[14px] text-erebus-text-1 leading-[1.8]">
              {renderMarkdown(msg.text)}
            </div>
            {msg.sources && (
              <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-white/[0.07]">
                {msg.sources.map((s, i) => (
                  <SourcePill
                    key={i}
                    source={s}
                    onOpen={onOpenSource}
                    onSourcePanelClick={() => onSourceClick(msg.sources)}
                  />
                ))}
              </div>
            )}
          </>
        )}

        {activeTab === 'sources' && (
          <div className="space-y-3">
            {!msg.sources?.length ? (
              <div className="flex flex-col items-center py-8 gap-2 opacity-50">
                <FileText size={24} className="text-erebus-text-3" />
                <p className="text-[12px] font-mono text-erebus-text-3">
                  Ask about a specific company (e.g. &quot;Infosys financials&quot;) to see live sources here.
                </p>
              </div>
            ) : (
              msg.sources.map((s, i) => (
                <div
                  key={i}
                  onClick={() => s.file_key && handleDownloadSource(s)}
                  className={`flex items-start gap-3 px-4 py-3.5 rounded-xl border border-white/[0.07] bg-erebus-bg ${s.file_key ? 'cursor-pointer hover:border-white/[0.15] hover:bg-white/[0.02] transition-all group' : ''
                    }`}
                >
                  {/* Type icon */}
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                    style={{
                      background: s.type === 'rag_chunk' ? 'rgba(74,143,231,0.10)' : 'rgba(201,168,76,0.10)',
                      border: s.type === 'rag_chunk' ? '1px solid rgba(74,143,231,0.20)' : '1px solid rgba(201,168,76,0.20)'
                    }}>
                    <FileText size={14} className={s.type === 'rag_chunk' ? 'text-erebus-blue' : 'text-erebus-gold'} />
                  </div>

                  <div className="flex-1 min-w-0">
                    {/* Label + type badge */}
                    <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                      <p className="text-[13px] font-semibold text-erebus-text-1">{s.label}</p>
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono tracking-wide ${s.type === 'rag_chunk' ? 'chip-blue' : 'chip-amber'
                        }`}>
                        {s.type === 'rag_chunk' ? 'RAG CHUNK' : 'LIVE DATA'}
                      </span>
                    </div>

                    {/* Page / year range */}
                    {s.page && (
                      <p className="text-[11px] font-mono text-erebus-text-3 mb-2">
                        📅 {s.page}
                      </p>
                    )}

                    {/* Chunk text (RAG sources) */}
                    {s.chunk_text && (
                      <div className="text-[11px] font-mono text-erebus-text-3 whitespace-pre-wrap leading-relaxed
                                      max-h-[120px] overflow-y-auto scrollbar-none
                                      px-3 py-2 rounded-lg bg-black/20">
                        <HighlightNumbers text={s.chunk_text} />
                      </div>
                    )}

                    {/* No chunk text — live data source summary */}
                    {!s.chunk_text && (
                      <p className="text-[11px] font-mono text-erebus-text-3">
                        Financial statements loaded from S3 data store — verified against filed reports.
                      </p>
                    )}                  </div>

                  {/* Download arrow */}
                  {s.file_key && (
                    <ExternalLink size={13} className="text-erebus-text-3 shrink-0 mt-1 opacity-0 group-hover:opacity-100 transition-opacity" />
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'data' && (
          <ChartPanel chartData={msg.chart_data ?? null} />
        )}
      </div>
    </div>
  )
}

// ── Thinking indicator ────────────────────────────────────────────
function ThinkingIndicator() {
  const stages = ['Retrieving context', 'Checking answerability', 'Generating answer', 'Verifying']
  const [stage, setStage] = useState(0)
  useEffect(() => {
    const t = setInterval(() => setStage(s => (s + 1) % stages.length), 1800)
    return () => clearInterval(t)
  }, [])
  return (
    <div className="flex items-center gap-3 mb-5">
      <div className="w-6 h-6 rounded-full flex items-center justify-center border border-erebus-gold/50 font-serif text-erebus-gold text-xs bg-erebus-gold/[0.08]">
        E
      </div>
      <div className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-erebus-surface border border-white/[0.07]">
        <span className="text-[12px] font-mono text-erebus-text-3 mr-1 transition-all duration-300">{stages[stage]}</span>
        {[0, 150, 300].map(d => (
          <span
            key={d}
            className="w-1 h-1 rounded-full bg-erebus-gold animate-[pulse-dot_1.2s_infinite]"
            style={{ animationDelay: `${d}ms` }}
          />
        ))}
      </div>
    </div>
  )
}

// ── File upload panel (real S3 presigned upload) ──────────────────
function FileUploadPanel({ onClose, onUploaded }) {
  return (
    <div className="mx-4 mb-3 rounded-xl overflow-hidden border border-white/[0.07]">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/[0.07] bg-erebus-surface">
        <span className="text-[12px] font-mono text-erebus-text-3">Upload to S3</span>
        <button onClick={onClose} className="text-erebus-text-3 hover:text-erebus-text-1 transition-colors">
          <X size={14} />
        </button>
      </div>
      <div className="px-4 py-4 bg-erebus-bg">
        <FileUploader
          prefix="uploads"
          compact
          label="Drop a document or click to browse"
          onSuccess={(result) => {
            onUploaded?.(result)
            onClose()
          }}
        />
      </div>
    </div>
  )
}

// ── Empty State ───────────────────────────────────────────────────
function EmptyState({ onSelect }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-8 gap-8">
      <div className="text-center">
        <div className="w-12 h-12 rounded-full flex items-center justify-center border-2 border-erebus-gold/40 font-serif text-erebus-gold text-2xl mx-auto mb-6 bg-erebus-gold/[0.08]">
          E
        </div>
        <h2 className="font-serif text-[30px] text-erebus-text-1 mb-2">
          What would you like to research?
        </h2>
        <p className="text-[14px] text-erebus-text-2 max-w-[440px] leading-relaxed">
          Ask about any NSE or BSE listed company financials, management guidance, peer comparison, or risk analysis. Every answer cites its source.
        </p>
      </div>

      {/* Suggestion chips */}
      <div className="flex flex-wrap justify-center gap-2 max-w-lg">
        {SUGGESTIONS.map(s => (
          <button
            key={s.label}
            onClick={() => onSelect(s.prompt)}
            className="flex items-center gap-2 px-4 py-2 rounded-full text-[13px] font-medium btn-ghost"
          >
            <Sparkles size={12} className="text-erebus-gold" />
            {s.label}
          </button>
        ))}
      </div>
    </div>
  )
}

// ── Chat Input ────────────────────────────────────────────────────
function ChatInput({ onSend, onAttach, model, onModelChange, disabled }) {
  const [text, setText] = useState('')
  const textareaRef = useRef(null)

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (text.trim() && !disabled) { onSend(text.trim()); setText('') }
    }
  }

  function handleSend() {
    if (text.trim() && !disabled) { onSend(text.trim()); setText('') }
  }

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px'
    }
  }, [text])

  return (
    <div className="px-4 pb-4 pt-2">
      {/* Single-row input box */}
      <div className="flex items-center gap-2 rounded-xl px-3 py-2.5 bg-erebus-surface border border-white/[0.10]">

        {/* Paperclip */}
        <button
          onClick={onAttach}
          className="p-1.5 rounded-md text-erebus-text-3 hover:text-erebus-gold hover:bg-[var(--gold-dim)] transition-all duration-150 shrink-0"
        >
          <Paperclip size={16} />
        </button>

        {/* Textarea — grows to fill space */}
        <textarea
          ref={textareaRef}
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder="Ask about any Indian listed company…"
          className="flex-1 bg-transparent text-[14px] text-erebus-text-1 placeholder:text-erebus-text-3 resize-none outline-none leading-relaxed py-0.5"
          style={{ maxHeight: '120px' }}
        />

        {/* Model selector — inline before send */}
        <div className="shrink-0">
          <ModelSelector value={model} onChange={onModelChange} disabled={disabled} />
        </div>

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={!text.trim() || disabled}
          className={`
            w-8 h-8 rounded-lg flex items-center justify-center shrink-0
            transition-all duration-150
            ${text.trim() && !disabled
              ? 'bg-erebus-gold text-erebus-bg hover:bg-erebus-gold-light active:scale-95'
              : 'bg-erebus-surface-2 text-erebus-text-3 cursor-not-allowed'
            }
          `}
        >
          <Send size={14} />
        </button>
      </div>

      <p className="text-center text-[11px] font-mono text-erebus-text-3 mt-2">
        EREBUS cites sources for every claim · Not investment advice
      </p>
    </div>
  )
}


// ── Source Text Highlighter ─────────────────────────────────────────
function HighlightNumbers({ text }) {
  if (!text) return null
  // Match sequences of digits, commas, dots, and optional % or x multipliers
  const parts = text.toString().split(/([\d,]+(?:\.\d+)?\s*%?)/)
  return (
    <>
      {parts.map((part, i) => {
        if (/^[\d,]+(?:\.\d+)?\s*%?$/.test(part)) {
          return (
            <span key={i} className="text-erebus-gold font-semibold bg-erebus-gold/[0.12] px-[2px] rounded mx-[1px]">
              {part}
            </span>
          )
        }
        return <span key={i}>{part}</span>
      })}
    </>
  )
}

// ── Context Panel (inline) ────────────────────────────────────────
function ContextPanel({ open, sources, onClose, onOpen }) {
  if (!open) return null
  return (
    <div className="w-72 shrink-0 border-l border-white/[0.07] flex flex-col bg-erebus-surface animate-[slide-in-right_0.25s_ease_forwards]">
      <div className="flex items-center justify-between px-4 py-3.5 border-b border-white/[0.07]">
        <div className="flex items-center gap-2">
          <FileText size={14} className="text-erebus-text-3" />
          <span className="text-[13px] font-medium text-erebus-text-1">Sources</span>
          <span className="text-[11px] font-mono chip-blue px-1.5 py-0.5 rounded">{sources.length}</span>
        </div>
        <button onClick={onClose} className="text-erebus-text-3 hover:text-erebus-text-1 transition-colors">
          <X size={15} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto scrollbar-none p-4 space-y-2">
        {sources.map((s, i) => (
          <div
            key={i}
            onClick={() => handleDownloadSource(s)}
            className={`p-3 rounded-lg bg-erebus-bg border border-white/[0.07] ${s.file_key ? 'cursor-pointer hover:border-white/[0.15] transition-colors group' : ''}`}
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex items-center gap-2 min-w-0">
                <FileText size={13} className="text-erebus-blue shrink-0" />
                <span className="text-[13px] font-medium text-erebus-text-1 truncate">{s.label}</span>
              </div>
              {s.file_key && (
                <ExternalLink size={12} className="text-erebus-text-3 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
              )}
            </div>
            <p className="text-[11px] font-mono text-erebus-text-3 whitespace-pre-wrap leading-relaxed">
              <HighlightNumbers text={s.chunk_text || s.page} />
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function ChatPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [messages, setMessages] = useState([])
  const [sessionId, setSessionId] = useState(searchParams.get('session_id') || null)
  
  const [panelOpen, setPanelOpen] = useState(false)
  const [activeSources, setActiveSources] = useState([])
  const [thinking, setThinking] = useState(false)
  const [showUpload, setShowUpload] = useState(false)
  const [model, setModel] = useState('quick')
  const [uploadedFiles, setUploadedFiles] = useState([])  // S3 results: { file_key, file_url }
  const bottomRef = useRef(null)
  
  const initiallyLoaded = useRef(false)
  const currentSessionRef = useRef(searchParams.get('session_id'))
  const isSavingRef = useRef(false)

  // 1. Load session from URL
  useEffect(() => {
    const sid = searchParams.get('session_id')
    if (sid && (!initiallyLoaded.current || sid !== currentSessionRef.current)) {
      initiallyLoaded.current = true
      currentSessionRef.current = sid
      setSessionId(sid)
      fetchSession(sid)
        .then(res => {
          if (res.session?.ui_state) setMessages(res.session.ui_state)
        })
        .catch(err => {
          console.error("Failed to load session:", err)
        })
    } else if (!sid && currentSessionRef.current) {
      // Clear out if URL param was removed
      currentSessionRef.current = null
      setSessionId(null)
      setMessages([])
    }
  }, [searchParams])

  // 2. Autosave Session State
  useEffect(() => {
    if (messages.length === 0) return

    if (!sessionId && !isSavingRef.current) {
      isSavingRef.current = true
      createSession({
        session_type: 'chat',
        title: messages[0].text.substring(0, 150),
        ui_state: messages
      })
      .then(res => {
        const newId = res.session.id.toString()
        currentSessionRef.current = newId
        setSessionId(newId)
        setSearchParams({ session_id: newId })
        isSavingRef.current = false
      })
      .catch(err => {
        console.error("Create session failed:", err)
        isSavingRef.current = false
      })
    } else if (sessionId) {
      // Update existing session seamlessly
      updateSession(sessionId, { ui_state: messages }).catch(console.error)
    }
  }, [messages, sessionId, setSearchParams])

  // FileViewer state
  const [viewerUrl, setViewerUrl] = useState(null)
  const [viewerName, setViewerName] = useState('')

  const handleOpenSource = useCallback(async (source) => {
    if (!source.s3_key) return
    try {
      const url = await getPresignedUrl(source.s3_key)
      // Use the real filename from s3_key so FileViewer can detect the extension.
      // e.g. "TCS/TCS_Data_Sheet.xlsx" → "TCS_Data_Sheet.xlsx"
      const realFileName = source.s3_key.split('/').pop() || source.label
      setViewerName(realFileName)
      setViewerUrl(url)
    } catch (e) {
      alert(e.message)
    }
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking])

  async function handleSend(text) {
    setMessages(prev => [...prev, { role: 'user', text }])
    setThinking(true)
    setShowUpload(false)

    const provider = PROVIDER_MAP[model] || 'gemini'

    // Build conversation history from prior messages (last 6 = 3 turns)
    const history = messages
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .slice(-6)
      .map(m => ({
        role: m.role,
        content: m.role === 'user' ? m.text : (m.text || ''),
      }))

    try {
      const resp = await chatWithErebus(text, provider, null, history)
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: resp.answer,
        sources: (resp.sources || []).map(s => ({
          label: s.label ?? 'Document',
          page: s.page ?? '—',
          chunk_text: s.chunk_text ?? null,
          file_key: s.file_key ?? null,
          type: s.type ?? 'live_data',
          s3_key: s.s3_key || null,
        })),
        table: null,
        chart_data: resp.chart_data ?? null,
        company_id: resp.company_id,
        context_loaded: resp.context_loaded,
        model_used: resp.model_used,
        confidence: resp.confidence ?? null,
        gates_passed: resp.gates_passed ?? null,
        failed_at: resp.failed_at ?? null,
      }])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'error',
        text: typeof err === 'string' ? err : 'Something went wrong. Please try again.',
      }])
    } finally {
      setThinking(false)
    }
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex h-full overflow-hidden">
      {/* Chat area */}
      <div className="flex flex-col flex-1 overflow-hidden min-w-0">
        {isEmpty && !thinking ? (
          <EmptyState onSelect={handleSend} />
        ) : (
          <div className="flex-1 overflow-y-auto scrollbar-none px-6 pt-6">
            <div className="max-w-2xl mx-auto">
              {messages.map((msg, i) => (
                <Message
                  key={i}
                  msg={msg}
                  onSourceClick={sources => {
                    setActiveSources(sources)
                    setPanelOpen(true)
                  }}
                  onOpenSource={handleOpenSource}
                />
              ))}
              {thinking && <ThinkingIndicator />}
              <div ref={bottomRef} />
            </div>
          </div>
        )}

        {/* File upload panel — real presigned S3 upload */}
        {showUpload && (
          <FileUploadPanel
            onClose={() => setShowUpload(false)}
            onUploaded={(result) => setUploadedFiles(prev => [...prev, result])}
          />
        )}

        {/* Uploaded files context strip */}
        {uploadedFiles.length > 0 && (
          <div className="mx-4 mb-2 flex items-center gap-2 flex-wrap">
            <span className="text-[10px] font-mono text-erebus-text-3">Context:</span>
            {uploadedFiles.map((f, i) => (
              <span
                key={i}
                className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-mono chip-green"
              >
                <CheckCircle size={9} />
                {f.file_key.split('/').pop()}
                <button
                  onClick={() => setUploadedFiles(prev => prev.filter((_, j) => j !== i))}
                  className="ml-0.5 opacity-60 hover:opacity-100 transition-opacity"
                >
                  <X size={9} />
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Input */}
        <ChatInput
          onSend={handleSend}
          onAttach={() => setShowUpload(v => !v)}
          model={model}
          onModelChange={setModel}
          disabled={thinking}
        />
      </div>

      {/* Context panel */}
      <ContextPanel
        open={panelOpen}
        sources={activeSources}
        onClose={() => setPanelOpen(false)}
        onOpen={handleOpenSource}
      />

      {/* File viewer modal */}
      <FileViewer
        url={viewerUrl}
        fileName={viewerName}
        onClose={() => { setViewerUrl(null); setViewerName('') }}
      />
    </div>
  )
}
