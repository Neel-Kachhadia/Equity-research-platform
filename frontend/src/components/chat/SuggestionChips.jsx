const SUGGESTIONS = [
  "Analyse HDFC Bank's margin trajectory",
  'Compare Titan vs Kalyan Jewellers ROE',
  'Management guidance hits for Asian Paints Q4',
  'Risk score for Adani Enterprises',
  'Top 3 pharma companies by FCF conversion',
]

export default function SuggestionChips({ onSelect }) {
  return (
    <div className="flex gap-2.5 overflow-x-auto pb-1 max-w-2xl w-full scrollbar-none">
      {SUGGESTIONS.map(s => (
        <button
          key={s}
          onClick={() => onSelect(s)}
          className="px-4 py-2.5 rounded-full text-[14px] text-erebus-text-2
                     bg-erebus-surface border border-white/[0.08]
                     hover:border-erebus-gold hover:text-erebus-text-1
                     whitespace-nowrap transition-all duration-200 shrink-0"
        >
          {s}
        </button>
      ))}
    </div>
  )
}
