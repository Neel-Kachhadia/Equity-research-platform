import { useState, useCallback } from 'react'

const NSE_TICKERS = [
  'HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'AXISBANK', 'SBIN',
  'TITAN', 'RELIANCE', 'TCS', 'INFY', 'WIPRO',
  'ASIANPAINT', 'PIDILITIND', 'NESTLEIND', 'HINDUNILVR',
  'SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB',
  'ADANIENT', 'ADANIPORTS', 'LT', 'POWERGRID',
]

export function useCompany() {
  const [query,       setQuery]       = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [selected,    setSelected]    = useState(null)

  const search = useCallback((q) => {
    setQuery(q)
    if (!q) { setSuggestions([]); return }
    setSuggestions(
      NSE_TICKERS
        .filter(t => t.toLowerCase().includes(q.toLowerCase()))
        .slice(0, 6)
    )
  }, [])

  const select = useCallback((ticker) => {
    setSelected(ticker)
    setQuery(ticker)
    setSuggestions([])
  }, [])

  return { query, suggestions, selected, search, select }
}
