// src/components/chat/MessageThread.jsx
import { useEffect, useRef } from 'react'
import AgentMessage from './AgentMessage'

export default function MessageThread({ messages, thinking, onSourceClick }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking])

  return (
    <div className="flex-1 overflow-y-auto px-4 md:px-6 py-6 space-y-6 scrollbar-none">
      {messages.map((msg, i) =>
        msg.role === 'user' ? (
          <div key={i} className="flex justify-end">
            <div>
              <div
                className="max-w-[70%] px-4 py-3 rounded-[12px_12px_2px_12px] text-[15px] text-erebus-text-1 leading-[1.7]"
                style={{ background: 'var(--gold-dim)', border: '1px solid rgba(201,168,76,0.20)' }}
              >
                {msg.text}
              </div>
              <p className="text-[11px] text-erebus-text-3 mt-1 text-right">Just now</p>
            </div>
          </div>
        ) : (
          <AgentMessage
            key={i}
            message={msg}
            onSourceClick={onSourceClick}
          />
        )
      )}

      {/* Thinking indicator */}
      {thinking && (
        <div className="flex items-start gap-3">
          <div
            className="w-7 h-7 rounded-full border border-erebus-gold/50 flex items-center justify-center font-serif text-erebus-gold text-sm shrink-0"
            style={{ background: 'var(--gold-dim)' }}
          >
            E
          </div>
          <div className="flex flex-col gap-1 pt-1">
            <div
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg"
              style={{ background: '#0F1117', border: '1px solid var(--border)' }}
            >
              {[0, 1, 2].map(idx => (
                <span
                  key={idx}
                  className="w-1.5 h-1.5 rounded-full bg-erebus-gold animate-pulse-dot"
                  style={{ animationDelay: `${idx * 0.2}s` }}
                />
              ))}
            </div>
            <p className="text-[11px] font-mono text-erebus-text-3 px-1">
              Retrieving context · Computing ratios · Generating insight
            </p>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
