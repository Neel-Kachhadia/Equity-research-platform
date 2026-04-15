// src/components/ui/ModelSelector.jsx
import { useState, useRef, useEffect } from 'react'
import { Zap, BarChart2, ChevronDown } from 'lucide-react'

const MODELS = [
  {
    id:       'quick',
    label:    'Quick',
    icon:     Zap,
    color:    'text-erebus-amber',
    tagline:  'Fast answers · lightweight analysis',
  },
  {
    id:       'deep',
    label:    'Deep',
    icon:     BarChart2,
    color:    'text-erebus-blue',
    tagline:  'Detailed reasoning · rich analysis',
  },
]

export default function ModelSelector({ value = 'quick', onChange, disabled = false }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  const current = MODELS.find(m => m.id === value) ?? MODELS[0]
  const CurrentIcon = current.icon

  useEffect(() => {
    function handler(e) { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => !disabled && setOpen(o => !o)}
        disabled={disabled}
        className={`
          flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg
          text-[12px] font-medium transition-all duration-150
          border border-white/[0.10] bg-erebus-surface-2
          hover:border-white/[0.18] hover:bg-erebus-surface-3
          disabled:opacity-50 disabled:cursor-not-allowed
          ${open ? 'border-white/[0.18]' : ''}
        `}
      >
        <CurrentIcon size={12} className={current.color} />
        <span className="text-erebus-text-2">{current.label}</span>
        <ChevronDown
          size={11}
          className={`text-erebus-text-3 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div className="absolute bottom-full mb-1.5 right-0 w-56 rounded-xl bg-erebus-surface-2 border border-white/[0.10] shadow-[0_8px_32px_rgba(0,0,0,0.5)] z-50 overflow-hidden">
          {MODELS.map(m => {
            const Icon = m.icon
            const active = m.id === value
            return (
              <button
                key={m.id}
                onClick={() => { onChange?.(m.id); setOpen(false) }}
                className={`
                  w-full flex items-start gap-3 px-4 py-3 text-left
                  transition-colors duration-150
                  ${active ? 'bg-white/[0.05]' : 'hover:bg-white/[0.03]'}
                `}
              >
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${active ? 'bg-erebus-surface-3' : 'bg-white/[0.04]'}`}>
                  <Icon size={13} className={m.color} />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[13px] font-medium text-erebus-text-1">{m.label}</span>
                    {active && (
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/[0.06] text-erebus-text-3">
                        Active
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-erebus-text-3">{m.tagline}</span>
                </div>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
