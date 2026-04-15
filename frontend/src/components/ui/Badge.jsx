// src/components/ui/Badge.jsx
// Uses named CSS classes from index.css — no old --erebus-* var names
export default function Badge({ children, variant = 'gold', className = '' }) {
  const variants = {
    gold:   'chip-gold',
    blue:   'chip-blue',
    green:  'chip-green',
    red:    'chip-red',
    amber:  'chip-amber',
    subtle: 'text-erebus-text-2',
  }

  const subtleStyle = variant === 'subtle'
    ? { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }
    : {}

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium ${variants[variant] ?? 'chip-gold'} ${className}`}
      style={subtleStyle}
    >
      {children}
    </span>
  )
}
