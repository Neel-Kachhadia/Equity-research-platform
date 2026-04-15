// src/components/analyze/AnalyzeResults.jsx
import { AlertTriangle, RefreshCw, BarChart3, TrendingUp, Activity, MessageSquare, Shield, Target } from 'lucide-react'

// ── Helpers ───────────────────────────────────────────────────────────────────

function pct(v, decimals = 1) {
  if (v == null) return '—'
  return `${(v * 100).toFixed(decimals)}%`
}

function num(v, decimals = 2) {
  if (v == null || v === '') return '—'
  if (typeof v === 'boolean') return v ? 'Yes' : 'No'
  if (typeof v === 'number') return Number.isInteger(v) ? v.toLocaleString() : v.toFixed(decimals)
  if (typeof v === 'string') return v
  if (Array.isArray(v)) return v.length ? v.slice(0, 3).join(', ') + (v.length > 3 ? '…' : '') : '—'
  if (typeof v === 'object') return null   // caller handles
  return '—'
}

function scoreColor(s) {
  if (s == null) return '#4E5262'
  if (s >= 75) return '#2ECC8A'
  if (s >= 50) return '#E09A25'
  return '#D95555'
}

function casColor(s) {
  if (s == null) return '#4E5262'
  if (s >= 20) return '#2ECC8A'
  if (s >= -20) return '#E09A25'
  return '#D95555'
}

// ── Primitives ────────────────────────────────────────────────────────────────

function SectionLabel({ children }) {
  return (
    <p className="text-[10px] font-mono text-erebus-text-3 uppercase tracking-[0.12em] mb-3">
      {children}
    </p>
  )
}

function SubLabel({ children }) {
  return (
    <p className="text-[9px] font-mono text-erebus-text-3 uppercase tracking-widest mt-3 mb-1.5 opacity-60">
      {children}
    </p>
  )
}

function KVRow({ label, value, accent, bar }) {
  const display = num(value)
  if (display === null) return null   // skip nested objects

  const barWidth = bar != null ? Math.min(Math.abs(bar) * 100, 100) : null
  const barColor = accent ?? '#4A8FE7'

  return (
    <div className="flex items-center justify-between py-1.5 border-b border-white/[0.04] last:border-0">
      <span className="text-[12px] text-erebus-text-2 capitalize">{label.replace(/_/g, ' ')}</span>
      <div className="text-right flex items-center gap-2">
        {barWidth != null && (
          <div className="w-16 h-1 rounded-full bg-white/[0.07] overflow-hidden">
            <div className="h-full rounded-full" style={{ width: `${barWidth}%`, background: barColor }} />
          </div>
        )}
        <span className="text-[12px] font-mono font-medium" style={{ color: accent ?? '#EEE9E0' }}>
          {display}
        </span>
      </div>
    </div>
  )
}

function DataCard({ title, icon: Icon, accentColor, children }) {
  return (
    <div className="elevated rounded-xl p-5" style={{ borderTop: `2px solid ${accentColor ?? 'rgba(255,255,255,0.07)'}` }}>
      <div className="flex items-center gap-2 mb-3">
        <Icon size={14} style={{ color: accentColor }} />
        <SectionLabel>{title}</SectionLabel>
      </div>
      {children}
    </div>
  )
}

// ── CAS Score dial ────────────────────────────────────────────────────────────

function CasDial({ cas, risk }) {
  if (cas == null && risk == null) return null
  return (
    <div className="flex gap-3 mb-4">
      {cas != null && (
        <div
          className="flex-1 rounded-xl flex flex-col items-center justify-center py-3"
          style={{ background: `${casColor(cas)}10`, border: `1px solid ${casColor(cas)}30` }}
        >
          <p className="text-[26px] font-mono font-semibold leading-none" style={{ color: casColor(cas) }}>
            {cas > 0 ? '+' : ''}{cas}
          </p>
          <p className="text-[9px] font-mono text-erebus-text-3 mt-1">CAS Score</p>
        </div>
      )}
      {risk != null && (
        <div
          className="flex-1 rounded-xl flex flex-col items-center justify-center py-3"
          style={{ background: `${scoreColor(100 - risk)}10`, border: `1px solid ${scoreColor(100 - risk)}30` }}
        >
          <p className="text-[26px] font-mono font-semibold leading-none" style={{ color: scoreColor(100 - risk) }}>
            {risk}
          </p>
          <p className="text-[9px] font-mono text-erebus-text-3 mt-1">Risk Score</p>
        </div>
      )}
    </div>
  )
}

// ── Ranking Card ──────────────────────────────────────────────────────────────

function RankingCard({ ranking }) {
  if (!ranking) return (
    <DataCard title="Ranking" icon={BarChart3} accentColor="#C9A84C">
      <p className="text-[12px] text-erebus-text-3 italic">No ranking data returned.</p>
    </DataCard>
  )

  const { cas, dci, qsd, risk_score, sector, note } = ranking
  const signals = ranking?.signal_card?.signals ?? {}

  return (
    <DataCard title="Ranking" icon={BarChart3} accentColor="#C9A84C">
      <CasDial cas={cas} risk={risk_score} />

      <KVRow label="DCI" value={dci != null ? dci.toFixed(1) : null} accent="#C9A84C" />
      <KVRow label="QSD" value={qsd != null ? qsd.toFixed(1) : null} accent="#C9A84C" />
      <KVRow label="Sector" value={sector} />

      {/* Normalised signal bars */}
      {Object.keys(signals).length > 0 && (
        <>
          <SubLabel>Signal Breakdown</SubLabel>
          {Object.entries(signals).map(([k, v]) => (
            typeof v === 'number' ? (
              <KVRow
                key={k}
                label={k}
                value={v.toFixed(1)}
                accent={casColor(v * 100)}
                bar={(v + 1) / 2}
              />
            ) : null
          ))}
        </>
      )}

      {note && <p className="text-[10px] font-mono text-erebus-text-3 mt-3 italic">{note}</p>}
    </DataCard>
  )
}

// ── Quant Card ────────────────────────────────────────────────────────────────

function QuantCard({ quant }) {
  if (!quant) return (
    <DataCard title="Quantitative Profile" icon={TrendingUp} accentColor="#4A8FE7">
      <p className="text-[12px] text-erebus-text-3 italic">No quantitative data returned.</p>
    </DataCard>
  )

  const ratios = quant.ratios ?? {}
  const risk = quant.risk ?? {}

  const keyRatios = ['net_margin', 'return_on_equity', 'return_on_assets',
    'debt_to_equity', 'interest_coverage', 'current_ratio', 'revenue_growth', 'earnings_growth']

  const riskScore = risk.overall_risk_score
  const riskCat = risk.risk_category

  return (
    <DataCard title="Quantitative Profile" icon={TrendingUp} accentColor="#4A8FE7">

      {/* Risk summary */}
      {riskScore != null && (
        <div className="flex items-center gap-2 mb-3 px-3 py-2 rounded-lg bg-white/[0.03]">
          <Shield size={12} className="text-erebus-blue shrink-0" />
          <span className="text-[11px] text-erebus-text-2">Risk:</span>
          <span className="text-[11px] font-mono font-semibold" style={{ color: scoreColor(100 - riskScore) }}>
            {riskScore.toFixed(0)} / 100
          </span>
          {riskCat && (
            <span className="text-[10px] font-mono text-erebus-text-3 uppercase ml-1">· {riskCat}</span>
          )}
        </div>
      )}

      <SubLabel>Key Ratios</SubLabel>
      {keyRatios.map(k => {
        const v = ratios[k]
        if (v == null) return null
        const isPct = k.endsWith('_margin') || k.endsWith('_growth') || k === 'return_on_equity' || k === 'return_on_assets'
        const display = isPct ? pct(v) : v.toFixed(2)
        const accent = k.endsWith('_growth') || k.endsWith('_margin') || k.startsWith('return')
          ? (v > 0 ? '#2ECC8A' : '#D95555')
          : '#EEE9E0'
        return <KVRow key={k} label={k} value={display} accent={accent} />
      })}

      {/* Risk factors */}
      {risk.risk_factors?.length > 0 && (
        <>
          <SubLabel>Risk Factors</SubLabel>
          <ul className="space-y-1">
            {risk.risk_factors.slice(0, 4).map((f, i) => (
              <li key={i} className="flex items-start gap-1.5 text-[11px] text-erebus-text-2">
                <span className="w-1 h-1 rounded-full bg-erebus-text-3 mt-1.5 shrink-0" />
                {f}
              </li>
            ))}
          </ul>
        </>
      )}
    </DataCard>
  )
}

// ── Alpha Card ────────────────────────────────────────────────────────────────

function AlphaCard({ alpha }) {
  if (!alpha) return (
    <DataCard title="Alpha Signals" icon={Activity} accentColor="#2ECC8A">
      <p className="text-[12px] text-erebus-text-3 italic">No alpha signal data returned.</p>
    </DataCard>
  )

  const composite = alpha.composite ?? {}
  const normalised = alpha.normalised_alphas ?? {}
  const flags = alpha.data_flags ?? {}

  const { company_id, company_name, sector } = alpha

  return (
    <DataCard title="Alpha Signals" icon={Activity} accentColor="#2ECC8A">

      {/* Composite row */}
      {Object.keys(composite).length > 0 && (
        <>
          <SubLabel>Composite</SubLabel>
          {Object.entries(composite).map(([k, v]) => {
            if (typeof v !== 'number') return null
            const color = k === 'cas' ? casColor(v) : (v >= 0.6 ? '#2ECC8A' : v >= 0.4 ? '#E09A25' : '#D95555')
            return <KVRow key={k} label={k.toUpperCase()} value={v.toFixed(2)} accent={color} />
          })}
        </>
      )}

      {/* Normalised alphas with bars */}
      {Object.keys(normalised).length > 0 && (
        <>
          <SubLabel>Normalised Signals</SubLabel>
          {Object.entries(normalised).map(([k, v]) => {
            if (typeof v !== 'number') return null
            const color = v >= 0.6 ? '#2ECC8A' : v >= 0.4 ? '#E09A25' : '#D95555'
            return (
              <KVRow
                key={k}
                label={k}
                value={`${(v * 100).toFixed(0)}`}
                accent={color}
                bar={v}
              />
            )
          })}
        </>
      )}

      {/* Data flags */}
      {Object.keys(flags).length > 0 && (
        <>
          <SubLabel>Data Flags</SubLabel>
          {Object.entries(flags).map(([k, v]) => (
            <KVRow key={k} label={k} value={typeof v === 'boolean' ? (v ? 'Yes' : 'No') : String(v)} />
          ))}
        </>
      )}

      {sector && <p className="text-[10px] font-mono text-erebus-text-3 mt-2">{company_name} · {sector}</p>}
    </DataCard>
  )
}

// ── Sentiment Card ────────────────────────────────────────────────────────────

function SentimentCard({ sentiment }) {
  if (!sentiment) return (
    <DataCard title="Sentiment" icon={MessageSquare} accentColor="#E09A25">
      <p className="text-[12px] text-erebus-text-3 italic">No sentiment data returned.</p>
    </DataCard>
  )

  const { score, label: slabel, available, trajectory, hedge_ratio, note } = sentiment

  return (
    <DataCard title="Sentiment" icon={MessageSquare} accentColor="#E09A25">
      {score != null && (
        <div className="flex items-center gap-2 mb-3">
          <div className="w-2 h-2 rounded-full" style={{ background: scoreColor(score) }} />
          <span className="text-[13px] font-mono font-semibold" style={{ color: scoreColor(score) }}>
            {score.toFixed(0)} / 100
          </span>
          {slabel && <span className="text-[11px] text-erebus-text-3 capitalize">· {slabel}</span>}
        </div>
      )}
      <KVRow label="Available" value={available} />
      <KVRow label="Trajectory" value={trajectory} />
      <KVRow label="Hedge Ratio" value={hedge_ratio != null ? hedge_ratio.toFixed(2) : null} />
      {note && <p className="text-[10px] font-mono text-erebus-text-3 mt-2 italic">{note}</p>}

      {/* Render any extra flat fields not explicitly handled */}
      {Object.entries(sentiment)
        .filter(([k]) => !['score', 'label', 'available', 'trajectory', 'hedge_ratio', 'note'].includes(k))
        .map(([k, v]) => {
          const d = num(v)
          if (d === null) return null
          return <KVRow key={k} label={k} value={d} />
        })
      }
    </DataCard>
  )
}

// ── Management Guidance Tracker Card ──────────────────────────────────────────

function GuidanceTrackerCard({ guidance }) {
  if (!guidance) return null;

  const { accuracy_hit_rate, hedge_ratio } = guidance;

  // Format into readable percentages
  const hitRatePct = (accuracy_hit_rate * 100).toFixed(0);
  const hedgePct = (hedge_ratio * 100).toFixed(1);

  return (
    <DataCard title="Management Guidance Tracker" icon={Target} accentColor="#E09A25">
      <div className="flex flex-col gap-4">
        {/* Track Record / Accuracy */}
        <div>
          <div className="flex justify-between items-end mb-1.5">
            <span className="text-[12px] text-erebus-text-2">Historical Target Hit-Rate</span>
            <span className="text-[14px] font-mono font-semibold" style={{ color: hitRatePct > 50 ? '#2ECC8A' : '#D95555' }}>
              {hitRatePct}%
            </span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-white/[0.07] overflow-hidden">
            <div className="h-full rounded-full" style={{ width: `${hitRatePct}%`, background: hitRatePct > 50 ? '#2ECC8A' : '#D95555' }} />
          </div>
          <p className="text-[10px] font-mono text-erebus-text-3 mt-2 italic">
            Measures delivered results vs. promised guidance over past quarters.
          </p>
        </div>

        {/* Hedge Language Metric */}
        <KVRow
          label="Hedge Language Ratio"
          value={`${hedgePct}%`}
          accent={hedge_ratio > 0.15 ? '#D95555' : '#2ECC8A'}
        />
        <p className="text-[10px] font-mono text-erebus-text-3 italic mt-[-4px]">
          Frequency of uncertainty qualifiers (e.g. "may", "could", "subject to") in transcripts.
        </p>

        {/* Latest Summary / Outlook */}
        {guidance.latest_summary && (
          <div className="mt-2 pt-4 border-t border-white/[0.04]">
            <span className="text-[10px] font-mono text-erebus-text-3 uppercase tracking-widest block mb-2">Platform Web Context</span>
            <p className="text-[11px] text-erebus-text-2 leading-relaxed whitespace-pre-wrap">
              {guidance.latest_summary}
            </p>
          </div>
        )}
      </div>
    </DataCard>
  )
}

// ── Explanation ───────────────────────────────────────────────────────────────

function ExplanationBlock({ text }) {
  if (!text) return null
  return (
    <div className="elevated rounded-xl p-5" style={{ borderLeft: '3px solid #C9A84C' }}>
      <div className="flex items-center gap-2 mb-3">
        <span className="section-label">AI Narrative</span>
        <span className="chip-gold text-[10px] font-mono px-2 py-0.5 rounded-full">deep mode</span>
      </div>
      <p className="text-[13px] text-erebus-text-2 leading-[1.8] whitespace-pre-wrap">{text}</p>
    </div>
  )
}

// ── Loading ───────────────────────────────────────────────────────────────────

function LoadingState({ mode }) {
  return (
    <div className="elevated rounded-xl p-8 flex flex-col items-center gap-4 text-center">
      <div className="relative w-12 h-12">
        <div className="absolute inset-0 rounded-full border-2 border-erebus-gold/20 border-t-erebus-gold animate-spin" style={{ animationDuration: '1s' }} />
        <div className="absolute inset-2 rounded-full border border-erebus-gold/10 border-b-erebus-gold/40 animate-spin" style={{ animationDuration: '1.5s', animationDirection: 'reverse' }} />
      </div>
      <div>
        <p className="text-[14px] font-mono font-medium text-erebus-text-1">
          {mode === 'deep' ? 'Running deep analysis…' : 'Analyzing company…'}
        </p>
        {mode === 'deep' && (
          <p className="text-[12px] font-mono text-erebus-text-3 mt-1 max-w-xs">
            Retrieving documents + generating LLM narrative.<br />This may take up to 30 seconds.
          </p>
        )}
      </div>
      <div className="flex gap-1.5">
        {[0, 1, 2].map(i => (
          <div key={i} className="w-1.5 h-1.5 rounded-full bg-erebus-gold animate-pulse-dot" style={{ animationDelay: `${i * 0.3}s` }} />
        ))}
      </div>
    </div>
  )
}

// ── Error ─────────────────────────────────────────────────────────────────────

function ErrorState({ message, onRetry }) {
  return (
    <div className="elevated rounded-xl p-6 flex flex-col items-center gap-4 text-center border-erebus-red/25">
      <div className="w-10 h-10 rounded-full flex items-center justify-center bg-erebus-red/[0.10]">
        <AlertTriangle size={18} className="text-erebus-red" />
      </div>
      <div>
        <p className="text-[13px] font-mono font-medium text-erebus-red mb-1">Analysis Failed</p>
        <p className="text-[12px] text-erebus-text-2 max-w-sm leading-relaxed">{message}</p>
      </div>
      <button id="analyze-retry-btn" onClick={onRetry} className="btn-ghost flex items-center gap-2 px-4 py-2 rounded-lg text-[12px] font-mono">
        <RefreshCw size={12} /> Retry
      </button>
    </div>
  )
}

// ── Idle ──────────────────────────────────────────────────────────────────────

function IdleState() {
  return (
    <div className="elevated rounded-xl p-8 flex flex-col items-center gap-3 text-center">
      <div className="w-10 h-10 rounded-full flex items-center justify-center font-serif text-erebus-gold bg-erebus-gold/[0.10] border border-erebus-gold/25">
        E
      </div>
      <p className="text-[13px] font-mono text-erebus-text-2">Enter a company ticker above and run an analysis.</p>
      <p className="text-[11px] font-mono text-erebus-text-3">Normal mode returns instantly. Deep mode includes AI narrative (~20–30 s).</p>
    </div>
  )
}

// ── Main export ───────────────────────────────────────────────────────────────

export default function AnalyzeResults({ status, response, error, mode, onRetry }) {
  if (status === 'idle') return <IdleState />
  if (status === 'loading') return <LoadingState mode={mode} />
  if (status === 'error') return <ErrorState message={error} onRetry={onRetry} />

  const ranking = response?.data?.ranking ?? null
  const quant = response?.data?.quant ?? null
  const alpha = response?.data?.alpha ?? null
  const guidance = response?.data?.alpha?.management_guidance ?? null
  const sentiment = response?.data?.sentiment ?? null
  const explanation = response?.explanation ?? null
  const companyId = response?.company_id ?? '—'
  const resMode = response?.mode ?? mode

  const hasAnyData = ranking || quant || alpha || sentiment || explanation
  if (!hasAnyData) {
    return (
      <div className="elevated rounded-xl p-6 text-center">
        <p className="text-[13px] font-mono text-erebus-text-3">
          Analysis completed but no data was returned for <span className="text-erebus-gold">{companyId}</span>.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="ticker text-erebus-gold">{companyId}</span>
          <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${resMode === 'deep' ? 'chip-amber' : 'chip-blue'}`}>
            {resMode} mode
          </span>
        </div>
        <span className="text-[10px] font-mono text-erebus-text-3">
          {new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>

      {/* Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <RankingCard ranking={ranking} />
        <QuantCard quant={quant} />
        <AlphaCard alpha={alpha} />
        <GuidanceTrackerCard guidance={guidance} />
        <SentimentCard sentiment={sentiment} />
      </div>

      <ExplanationBlock text={explanation} />
    </div>
  )
}
