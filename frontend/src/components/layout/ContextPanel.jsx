// src/components/layout/ContextPanel.jsx
import { X, FileText, ExternalLink } from 'lucide-react'

export default function ContextPanel({ open, sources, onClose }) {
  return (
    <div
      className={`
        h-full border-l border-white/[0.06] bg-erebus-bg
        flex flex-col shrink-0
        transition-all duration-[280ms] ease-out
        ${open ? 'w-80' : 'w-0 overflow-hidden'}
      `}
    >
      {open && (
        <>
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
            <div className="flex items-center gap-2">
              <FileText size={14} className="text-erebus-text-3" />
              <h3 className="text-[14px] font-medium text-erebus-text-1">Sources</h3>
              {sources?.length > 0 && (
                <span className="chip-blue text-[10px] font-mono px-1.5 py-0.5 rounded">
                  {sources.length}
                </span>
              )}
            </div>
            <button
              onClick={onClose}
              className="text-erebus-text-3 hover:text-erebus-text-1 transition-colors"
            >
              <X size={15} />
            </button>
          </div>

          {/* Source cards */}
          <div className="flex-1 overflow-y-auto scrollbar-none px-4 py-4 space-y-3">
            {(sources ?? []).map((src, i) => (
              <div
                key={i}
                className="bg-erebus-surface rounded-lg border border-white/[0.07] p-4"
              >
                <div className="flex items-start gap-2 mb-2">
                  <FileText size={14} className="text-erebus-blue shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-medium text-erebus-text-1 truncate">
                      {typeof src === 'string' ? src.split(' · ')[0] : src.label ?? src.title}
                    </p>
                    <p className="text-[12px] font-mono text-erebus-text-3 truncate">
                      {typeof src === 'string' ? src.split(' · ')[1] ?? src : src.page ?? src.ref}
                    </p>
                  </div>
                  <span className="chip-green text-[10px] px-1.5 py-0.5 rounded ml-auto shrink-0">HIGH</span>
                </div>

                <div className="border-l-2 border-erebus-gold/40 pl-3 py-1 bg-erebus-gold/[0.04] rounded-r">
                  <p className="text-[12px] text-erebus-text-2 leading-[1.6] italic">
                    "Net interest margin stood at 3.63% for Q4 FY24, compared to 3.91% in Q4 FY23..."
                  </p>
                </div>
                <button className="flex items-center gap-1 text-[12px] text-erebus-gold hover:underline mt-2">
                  View full document
                  <ExternalLink size={10} />
                </button>
              </div>
            ))}

            {(!sources || sources.length === 0) && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <FileText size={28} className="text-erebus-text-3 mb-3" />
                <p className="text-[13px] text-erebus-text-3">
                  Select a source pill to view citations
                </p>
              </div>
            )}
          </div>

          {/* Data Confidence Index */}
          <div className="px-4 pb-4 pt-4 border-t border-white/[0.06]">
            <p className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-wider mb-3">
              Data Confidence
            </p>
            {[
              { label: 'Source quality',    score: 92 },
              { label: 'Coverage',          score: 78 },
              { label: 'Freshness',         score: 85 },
              { label: 'Cross-validation',  score: 71 },
            ].map(item => (
              <div key={item.label} className="flex items-center gap-2.5 mb-2">
                <span className="text-[11px] font-mono text-erebus-text-3 w-28 shrink-0">{item.label}</span>
                <div className="flex-1 h-1 rounded-full bg-white/[0.06] overflow-hidden">
                  <div
                    className="h-full rounded-full bg-erebus-green bar-fill"
                    style={{ width: item.score + '%' }}
                  />
                </div>
                <span className="font-mono text-[11px] text-erebus-text-2 w-6 text-right">{item.score}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
