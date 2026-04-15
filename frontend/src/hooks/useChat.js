import { useState, useCallback } from 'react'

export function useChat() {
  const [messages, setMessages] = useState([])
  const [thinking, setThinking] = useState(false)

  const sendMessage = useCallback(async (text) => {
    setMessages(prev => [...prev, { role: 'user', text }])
    setThinking(true)

    try {
      // Replace with real EREBUS API call
      // const res = await fetch('/api/chat', { method: 'POST', body: JSON.stringify({ query: text }) })
      // const data = await res.json()
      await new Promise(r => setTimeout(r, 2000))
      setMessages(prev => [...prev, {
        role:    'assistant',
        text:    `Analysis for: "${text}". EREBUS has processed this query across all available filings.`,
        sources: ['Source Doc · p.1'],
      }])
    } catch (err) {
      console.error('Chat error:', err)
    } finally {
      setThinking(false)
    }
  }, [])

  const clearMessages = useCallback(() => setMessages([]), [])

  return { messages, thinking, sendMessage, clearMessages }
}
