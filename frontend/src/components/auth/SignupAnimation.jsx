import { useState, useEffect } from 'react'

const PERSONAS = [
  { label: 'Retail Analyst',  initials: 'RA' },
  { label: 'Fund Manager',    initials: 'FM' },
  { label: 'Researcher',      initials: 'RS' },
]

const REPORT_LINES = [
  'Revenue growth of 26% YoY driven by jewellery segment...',
  'EBITDA margin expanded 180bps to 11.4% in Q4 FY24...',
  'Management guided for 18-20% volume growth in FY25...',
]

const ALPHA_LABELS = ['Growth', 'Margin', 'Risk', 'Consistency', 'Sentiment']

export default function SignupAnimation() {
  const [phase, setPhase] = useState(0)
  const [visibleLines, setVisibleLines] = useState(0)

  useEffect(() => {
    const timings = [2000, 2500, 2000, 1500]
    const timer = setTimeout(() => {
      setPhase(p => (p + 1) % 4)
      if (phase === 1) setVisibleLines(0)
    }, timings[phase])
    return () => clearTimeout(timer)
  }, [phase])

  useEffect(() => {
    if (phase !== 1) return
    let count = 0
    const iv = setInterval(() => {
      count++
      setVisibleLines(count)
      if (count >= REPORT_LINES.length) clearInterval(iv)
    }, 600)
    return () => clearInterval(iv)
  }, [phase])

  const visible = (p) =>
    phase === p
      ? 'opacity-100 scale-100 translate-y-0'
      : 'opacity-0 scale-95 translate-y-2 pointer-events-none'

  return (
    <div className="flex-[0_0_55%] relative bg-erebus-bg overflow-hidden
                    flex items-center justify-center hidden lg:flex">

      {/* Phase 0 — Persona cards */}
      <div className={`absolute inset-0 flex items-center justify-center
                       transition-all duration-500 ${visible(0)}`}>
        <div className="flex flex-col gap-3">
          {PERSONAS.map((p, i) => (
            <div
              key={p.label}
              className="flex items-center gap-3 bg-erebus-surface
                         rounded-xl px-4 py-3 shadow-lg"
              style={{ border: '1px solid var(--border)', transform: `translateX(${(i - 1) * 12}px)` }}
            >
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center text-erebus-gold text-[12px] font-semibold"
                style={{ background: 'var(--gold-dim)' }}
              >
                {p.initials}
              </div>
              <span className="text-[14px] text-erebus-text-1">{p.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Phase 1 — Research report typewriter */}
      <div className={`absolute inset-0 flex items-center justify-center
                       transition-all duration-500 ${visible(1)}`}>
        <div className="w-72 bg-erebus-surface rounded-xl p-5 shadow-xl"
             style={{ border: '1px solid var(--border)' }}>
          <p className="font-mono text-[10px] text-erebus-text-3 mb-3 tracking-[0.08em]">
            RESEARCH OUTPUT · TITAN COMPANY
          </p>
          <div className="text-[13px] text-erebus-text-2 leading-[1.8] space-y-1">
            {REPORT_LINES.map((line, i) => (
              <p
                key={i}
                className={`transition-all duration-500 ${i < visibleLines ? 'opacity-100' : 'opacity-0'}`}
              >
                {line}
              </p>
            ))}
          </div>
        </div>
      </div>

      {/* Phase 2 — Confidence bars */}
      <div className={`absolute inset-0 flex items-center justify-center
                       transition-all duration-500 ${visible(2)}`}>
        <div className="w-72 bg-erebus-surface rounded-xl p-5 shadow-xl"
             style={{ border: '1px solid var(--border)' }}>
          <p className="font-mono text-[11px] text-erebus-text-3 mb-4">ALPHA SIGNAL CONFIDENCE</p>
          {ALPHA_LABELS.map((label, i) => (
            <div key={label} className="flex items-center gap-3 mb-3">
              <span className="text-[12px] text-erebus-text-2 w-24 shrink-0">{label}</span>
              <div className="flex-1 h-1 bg-white/[0.06] rounded-full overflow-hidden">
                <div
                  className="h-full bg-erebus-blue rounded-full bar-fill"
                  style={{ width: `${55 + i * 8}%` }}
                />
              </div>
              <span className="font-mono text-[11px] text-erebus-text-1">
                {55 + i * 8}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Phase 3 — Comparison table */}
      <div className={`absolute inset-0 flex items-center justify-center
                       transition-all duration-500 ${visible(3)}`}>
        <div className="bg-erebus-surface rounded-xl overflow-hidden shadow-xl"
             style={{ border: '1px solid var(--border)' }}>
          <table className="text-[12px]">
            <thead>
              <tr className="bg-white/[0.04]">
                {['Company', 'ROE', 'FCF', 'Score'].map(h => (
                  <th key={h} className="px-4 py-2.5 text-left font-mono text-erebus-text-3 font-normal tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                ['TITAN',      '31.2%', 'HIGH',  '82'],
                ['KALYANKJIL', '18.4%', 'MED',   '64'],
                ['SENCO',      '14.1%', 'LOW',   '51'],
              ].map((row, i) => (
                <tr key={i} className={i % 2 === 1 ? 'bg-white/[0.02]' : ''}>
                  {row.map((cell, j) => (
                    <td key={j} className={`px-4 py-2.5 ${
                      cell === 'HIGH' ? 'text-erebus-green' :
                      cell === 'MED'  ? 'text-erebus-amber' :
                      cell === 'LOW'  ? 'text-erebus-red'   :
                      j === 0         ? 'font-mono text-erebus-gold' :
                      'text-erebus-text-1'
                    }`}>
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <p className="absolute bottom-5 left-1/2 -translate-x-1/2
                    font-mono text-[10px] text-erebus-text-3 tracking-[0.1em] whitespace-nowrap">
        EREBUS · RETRIEVAL & KNOWLEDGE · QUANTITATIVE CORE · NLP SIGNAL
      </p>
    </div>
  )
}
