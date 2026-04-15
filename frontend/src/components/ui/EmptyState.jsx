// src/components/ui/EmptyState.jsx
export default function EmptyState({ icon: Icon, title, subtitle, action, className = '' }) {
  return (
    <div className={`flex flex-col items-center justify-center py-16 text-center px-8 ${className}`}>
      {Icon && (
        <div className="w-14 h-14 rounded-xl bg-white/[0.04] border border-white/[0.07] flex items-center justify-center mb-5">
          <Icon size={22} className="text-erebus-text-3" />
        </div>
      )}
      <h3 className="text-[15px] font-medium text-erebus-text-2 mb-2">{title}</h3>
      {subtitle && (
        <p className="text-[13px] text-erebus-text-3 max-w-xs leading-relaxed">{subtitle}</p>
      )}
      {action && (
        <button
          onClick={action.onClick}
          className="mt-5 px-4 py-2 text-[13px] font-medium rounded-lg btn-ghost"
        >
          {action.label}
        </button>
      )}
    </div>
  )
}
