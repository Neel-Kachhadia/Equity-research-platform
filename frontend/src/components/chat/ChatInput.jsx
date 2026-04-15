// src/components/chat/ChatInput.jsx
import { useState, useRef } from 'react'
import { Paperclip, X, Send, Tag } from 'lucide-react'

export default function ChatInput({ onSend }) {
  const [text,        setText]        = useState('')
  const [attachments, setAttachments] = useState([])
  const textareaRef                   = useRef(null)
  const fileRef                       = useRef(null)

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleSend() {
    if (!text.trim()) return
    onSend?.(text.trim())
    setText('')
    setAttachments([])
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  function handleChange(e) {
    setText(e.target.value)
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 200) + 'px'
  }

  function handleFileChange(e) {
    const files = Array.from(e.target.files)
    setAttachments(prev => [...prev, ...files])
  }

  return (
    <div
      className="px-4 md:px-6 pb-4 pt-2"
      style={{ background: 'linear-gradient(transparent, #080A0F 55%)' }}
    >
      {/* Attachment pills */}
      {attachments.length > 0 && (
        <div className="flex gap-2 mb-2 flex-wrap">
          {attachments.map((f, i) => (
            <div
              key={i}
              className="flex items-center gap-2 px-2.5 py-1.5 rounded-md text-[12px] text-erebus-text-2"
              style={{ background: '#151921', border: '1px solid rgba(255,255,255,0.08)' }}
            >
              <Paperclip size={11} className="shrink-0 text-erebus-blue" />
              <span className="max-w-[140px] truncate">{f.name}</span>
              <button
                onClick={() => setAttachments(prev => prev.filter((_, j) => j !== i))}
                className="text-erebus-text-3 hover:text-erebus-red transition-colors ml-1"
              >
                <X size={11} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input box */}
      <div
        className="rounded-[14px] px-4 py-3 transition-all duration-200"
        style={{ background: '#0F1117', border: '1px solid rgba(255,255,255,0.10)' }}
      >
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder="Ask about any listed Indian company…"
          className="w-full bg-transparent text-[15px] text-erebus-text-1
                     placeholder:text-erebus-text-3 outline-none resize-none
                     max-h-[200px] leading-[1.6]"
        />

        {/* Toolbar */}
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center gap-2">
            {/* File attach */}
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              className="p-1.5 rounded-md text-erebus-text-3 hover:text-erebus-gold hover:bg-[var(--gold-dim)] transition-all duration-150"
            >
              <Paperclip size={15} />
            </button>
            <input
              ref={fileRef}
              type="file"
              multiple
              accept=".pdf,.txt,.json,.csv,.xlsx"
              className="hidden"
              onChange={handleFileChange}
            />
            {/* Company tag */}
            <button
              type="button"
              className="flex items-center gap-1.5 text-[12px] font-mono text-erebus-text-3 hover:text-erebus-text-2 transition-colors px-2 py-1 rounded"
              style={{ border: '1px solid rgba(255,255,255,0.08)' }}
            >
              <Tag size={11} />
              Company
            </button>
          </div>

          {/* Send button */}
          <button
            onClick={handleSend}
            disabled={!text.trim()}
            className="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-150 active:scale-95"
            style={text.trim()
              ? { background: '#C9A84C', color: '#080A0F' }
              : { background: '#151921', color: '#4E5262', cursor: 'not-allowed' }
            }
          >
            <Send size={14} />
          </button>
        </div>
      </div>

      <p className="text-center text-[12px] text-erebus-text-3 mt-2 opacity-60">
        EREBUS cites every claim · Responses are for research only, not investment advice
      </p>
    </div>
  )
}
