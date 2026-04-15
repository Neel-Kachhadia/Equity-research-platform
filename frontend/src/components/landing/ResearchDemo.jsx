import { useEffect, useRef, useState } from 'react'
import gsap from 'gsap'
import ScrollTrigger from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const RESPONSE_LINES = [
  { delay: 0,    text: 'EREBUS SCORE:  74 / 100',                     color: '#C9A84C' },
  { delay: 350,  text: 'Moat:          Strong (dominant market share)', color: '#EEE9E0' },
  { delay: 700,  text: 'NIM:           3.63% — below guidance by 7bps',color: '#E09A25' },
  { delay: 1050, text: 'Risk Alpha:    Elevated (3-quarter miss streak)',color: '#D95555' },
  { delay: 1400, text: 'Sources:       Annual Report FY24 · Q4 Concall', color: '#4A8FE7' },
]

export default function ResearchDemo() {
  const sectionRef = useRef(null)
  const headerRef  = useRef(null)
  const terminalRef = useRef(null)
  const timerRef   = useRef(null)

  const [ticker,  setTicker]  = useState('')
  const [phase,   setPhase]   = useState('idle')
  const [lines,   setLines]   = useState([])
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.set(headerRef.current, { y: 30, opacity: 0 })
      gsap.set(terminalRef.current, { y: 50, opacity: 0, scale: 0.97 })

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 72%',
          once: true,
        },
      })

      tl.to(headerRef.current, { y: 0, opacity: 1, duration: 0.7, ease: 'power3.out' })
      tl.to(terminalRef.current, { y: 0, opacity: 1, scale: 1, duration: 0.75, ease: 'power3.out' }, '-=0.3')
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  useEffect(() => () => clearInterval(timerRef.current), [])

  function runDemo() {
    if (phase !== 'idle' || !ticker) return
    setPhase('thinking')
    setLines([])
    let ms = 0
    timerRef.current = setInterval(() => { ms += 100; setElapsed(ms / 1000) }, 100)
    setTimeout(() => {
      clearInterval(timerRef.current)
      setPhase('done')
      RESPONSE_LINES.forEach(l => setTimeout(() => setLines(p => [...p, l]), l.delay))
    }, 2200)
  }

  function reset() { setPhase('idle'); setLines([]); setElapsed(0); setTicker('') }

  return (
    <section ref={sectionRef} className="erebus-section bg-erebus-bg">
      <div ref={headerRef}>
        <p className="section-label text-center mb-4">Live Demo</p>
        <h2 className="font-dm-serif text-[clamp(1.8rem,4vw,3rem)] text-center mb-4"
            style={{ color: '#EEE9E0', letterSpacing: '-0.02em' }}>
          Watch the AI analyse.
        </h2>
        <p className="text-center text-[15px] mb-10" style={{ color: '#8A8D9A' }}>
          Enter any NSE/BSE ticker and hit Analyze.
        </p>
      </div>

      <div ref={terminalRef} className="max-w-2xl mx-auto gold-border elevated rounded-xl overflow-hidden">
        {/* Terminal chrome */}
        <div className="flex items-center gap-2 px-5 py-3"
             style={{ background: '#0A0C10', borderBottom: '1px solid rgba(201,168,76,0.12)' }}>
          <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#D95555' }} />
          <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#E09A25' }} />
          <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#2ECC8A' }} />
          <span className="font-jetbrains text-[11px] ml-3" style={{ color: '#4E5262' }}>
            erebus.research — ticker query
          </span>
        </div>

        <div className="p-6">
          <div className="flex gap-3 mb-6">
            <input
              value={ticker}
              onChange={e => setTicker(e.target.value.toUpperCase())}
              onKeyDown={e => e.key === 'Enter' && runDemo()}
              placeholder="e.g. HDFCBANK"
              className="input-erebus flex-1 font-jetbrains text-[14px] px-4 py-3 rounded-lg"
              style={{ background: '#080A0F', border: '1px solid rgba(255,255,255,0.10)', color: '#EEE9E0' }}
              disabled={phase !== 'idle'}
            />
            {phase === 'idle'
              ? <button onClick={runDemo} className="cta-button-primary rounded-lg px-6 text-[14px]">Analyze</button>
              : <button onClick={reset}   className="cta-button-secondary rounded-lg px-6 text-[14px]">Reset</button>
            }
          </div>

          {phase === 'thinking' && (
            <div className="flex items-center gap-3 py-4">
              <span className="font-jetbrains text-[13px]" style={{ color: '#8A8D9A' }}>Scanning documents</span>
              <span className="erebus-pulse-dot" /><span className="erebus-pulse-dot" /><span className="erebus-pulse-dot" />
              <span className="ml-auto font-jetbrains text-[11px]" style={{ color: '#4E5262' }}>{elapsed.toFixed(1)}s</span>
            </div>
          )}

          {phase === 'done' && (
            <div className="space-y-3">
              <p className="erebus-label mb-4">{ticker} · EREBUS ANALYSIS</p>
              {lines.map((line, i) => (
                <div key={i} className="font-jetbrains text-[13px] leading-[1.7] animate-fade-in" style={{ color: line.color }}>
                  {line.text}
                </div>
              ))}
              {lines.length === RESPONSE_LINES.length && (
                <p className="font-jetbrains text-[11px] mt-5 pt-4 animate-fade-in"
                   style={{ borderTop: '1px solid rgba(255,255,255,0.06)', color: '#4E5262' }}>
                  Demo output · Actual queries reason across 10K+ real documents
                </p>
              )}
            </div>
          )}

          {phase === 'idle' && (
            <div className="text-center py-4 font-jetbrains text-[12px]" style={{ color: '#4E5262' }}>
              Try: HDFCBANK · TITAN · INFY · RELIANCE
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
