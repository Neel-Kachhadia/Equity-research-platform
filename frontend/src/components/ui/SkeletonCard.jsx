// src/components/ui/SkeletonCard.jsx
export default function SkeletonCard({ lines = 3, height = '', className = '' }) {
  return (
    <div className={`elevated rounded-xl p-5 animate-pulse ${height} ${className}`}>
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 rounded-lg bg-white/[0.07]" />
        <div className="flex-1 space-y-1.5">
          <div className="h-2.5 bg-white/[0.07] rounded w-2/5" />
          <div className="h-2 bg-white/[0.04] rounded w-1/3" />
        </div>
      </div>
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={`h-2.5 bg-white/[0.05] rounded ${i === lines - 1 ? 'w-3/5' : 'w-full'}`}
          />
        ))}
      </div>
    </div>
  )
}

export function SkeletonRow({ className = '' }) {
  return (
    <div className={`flex items-center gap-4 px-4 py-3 border-b border-white/[0.05] animate-pulse ${className}`}>
      <div className="w-20 h-2.5 bg-white/[0.07] rounded" />
      <div className="flex-1 h-2.5 bg-white/[0.05] rounded" />
      <div className="w-16 h-2.5 bg-white/[0.05] rounded" />
      <div className="w-12 h-2.5 bg-white/[0.07] rounded" />
    </div>
  )
}

export function SkeletonText({ lines = 2, className = '' }) {
  return (
    <div className={`space-y-2 animate-pulse ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className={`h-2.5 bg-white/[0.05] rounded ${i === lines - 1 ? 'w-4/5' : 'w-full'}`} />
      ))}
    </div>
  )
}
