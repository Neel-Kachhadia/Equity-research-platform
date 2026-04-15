// src/components/chat/AgentMessage.jsx
import ReactMarkdown from 'react-markdown'
import { FileText, Copy, RefreshCw, ThumbsUp, ThumbsDown, FolderOpen } from 'lucide-react'

export default function AgentMessage({ message, onSourceClick }) {
  const { text, sources, table } = message

  return (
    <div className="flex items-start gap-3">
      {/* Avatar */}
      <div
        className="w-7 h-7 rounded-full border border-erebus-gold/50 flex items-center justify-center font-serif text-erebus-gold text-sm shrink-0 mt-0.5"
        style={{ background: 'var(--gold-dim)' }}
      >
        E
      </div>

      <div className="flex-1 min-w-0 space-y-3">
        {/* Source pills */}
        {sources?.length > 0 && (
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
            {sources.map((src, i) => (
              <button
                key={i}
                onClick={() => onSourceClick?.(sources)}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-md
                           text-[12px] font-mono text-erebus-text-2 shrink-0
                           hover:text-erebus-gold transition-all duration-150"
                style={{ background: '#151921', border: '1px solid rgba(255,255,255,0.08)' }}
              >
                <FileText size={11} className="shrink-0" />
                {src}
              </button>
            ))}
          </div>
        )}

        {/* Main text — markdown rendered */}
        <div className="erebus-md text-[15px] text-erebus-text-1 leading-[1.75]">
          <ReactMarkdown
            components={{
              h1: ({ children }) => <h1 className="text-[18px] font-semibold text-erebus-text-1 mb-2 mt-4">{children}</h1>,
              h2: ({ children }) => <h2 className="text-[16px] font-semibold text-erebus-text-1 mb-1.5 mt-3">{children}</h2>,
              h3: ({ children }) => <h3 className="text-[15px] font-medium text-erebus-gold mb-1 mt-2">{children}</h3>,
              p:  ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
              strong: ({ children }) => <strong className="font-semibold text-erebus-text-1">{children}</strong>,
              em: ({ children }) => <em className="italic text-erebus-text-2">{children}</em>,
              ul: ({ children }) => <ul className="list-disc list-outside pl-5 space-y-1 mb-2">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal list-outside pl-5 space-y-1 mb-2">{children}</ol>,
              li: ({ children }) => <li className="text-erebus-text-1">{children}</li>,
              code: ({ inline, children }) =>
                inline
                  ? <code className="px-1.5 py-0.5 rounded text-[13px] font-mono" style={{ background: '#0F1117', color: 'var(--gold)' }}>{children}</code>
                  : <pre className="p-3 rounded-lg overflow-x-auto text-[13px] font-mono mb-2" style={{ background: '#0F1117', border: '1px solid var(--border)', color: '#e2e8f0' }}><code>{children}</code></pre>,
              blockquote: ({ children }) => <blockquote className="pl-3 border-l-2 border-erebus-gold/40 text-erebus-text-2 italic my-2">{children}</blockquote>,
              hr: () => <hr className="my-3" style={{ borderColor: 'var(--border)' }} />,
            }}
          >
            {text}
          </ReactMarkdown>
        </div>

        {/* Financial table */}
        {table && (
          <div
            className="rounded-lg overflow-hidden"
            style={{ border: '1px solid var(--border)' }}
          >
            <table className="w-full">
              <thead>
                <tr style={{ background: 'rgba(255,255,255,0.04)' }}>
                  {table.headers.map(h => (
                    <th key={h} className="px-4 py-2.5 text-left text-[12px] font-mono text-erebus-text-3 tracking-[0.05em] font-normal">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.rows.map((row, i) => (
                  <tr key={i} style={{ background: i % 2 === 1 ? 'rgba(255,255,255,0.02)' : 'transparent', borderTop: '1px solid var(--border)' }}>
                    {row.map((cell, j) => (
                      <td
                        key={j}
                        className={`px-4 py-2.5 text-[14px] font-mono ${
                          typeof cell === 'string' && cell.startsWith('+') ? 'data-pos'
                          : typeof cell === 'string' && (cell.startsWith('-') || cell.startsWith('−')) ? 'data-neg'
                          : 'text-erebus-text-1'
                        }`}
                      >
                        {cell === 'HIGH' && <span className="px-2 py-0.5 rounded-full text-[11px] chip-green">HIGH</span>}
                        {cell === 'MED'  && <span className="px-2 py-0.5 rounded-full text-[11px] chip-amber">MED</span>}
                        {cell === 'LOW'  && <span className="px-2 py-0.5 rounded-full text-[11px] chip-red">LOW</span>}
                        {!['HIGH','MED','LOW'].includes(cell) && cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Follow-up chips */}
        <div className="flex gap-2 flex-wrap">
          {[
            'Dig deeper into risk factors',
            'Compare with peers',
            'Show 4-quarter trend',
          ].map(chip => (
            <button
              key={chip}
              className="px-3.5 py-1.5 rounded-full text-[13px] text-erebus-text-2 transition-all duration-200 hover:text-erebus-text-1"
              style={{ background: '#0F1117', border: '1px solid rgba(255,255,255,0.08)' }}
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Action row */}
        <div className="flex items-center gap-4">
          {[
            { icon: Copy,      label: 'Copy'       },
            { icon: RefreshCw, label: 'Regenerate' },
            { icon: FolderOpen,label: 'Sources'    },
            { icon: ThumbsUp,  label: ''           },
            { icon: ThumbsDown,label: ''           },
          ].map(({ icon: Icon, label }, i) => (
            <button
              key={i}
              className="flex items-center gap-1.5 text-[12px] text-erebus-text-3 hover:text-erebus-text-2 transition-colors"
            >
              <Icon size={13} />
              {label && <span className="hidden sm:inline">{label}</span>}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
