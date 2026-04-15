// src/components/auth/LoginAnimation.jsx
// GSAP 5-phase cinematic loop — no emojis, all icon-driven
import { useEffect, useRef } from 'react'
import { FileText, BarChart3, FileSpreadsheet } from 'lucide-react'
import gsap from 'gsap'

const ALPHA_LABELS = [
  'Growth', 'Margin', 'Risk', 'Credibility',
  'Volatility', 'Consistency', 'Sentiment', 'Rel.Strength',
]

const ALPHA_VALUES = [74, 58, 61, 64, 70, 72, 77, 65]

const DOCS = [
  { Icon: FileText,        label: 'Annual Report FY24'     },
  { Icon: FileText,        label: 'Q4 Earnings Transcript' },
  { Icon: FileSpreadsheet, label: 'Balance Sheet FY24.csv' },
]

export default function LoginAnimation() {
  const containerRef = useRef(null)
  const docRefs      = useRef([])
  const radarRefs    = useRef([])
  const eMarkRef     = useRef(null)
  const badgeRefs    = useRef([])
  const scorecardRef = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ repeat: -1, repeatDelay: 0.5 })

      // ── Set initial states ──────────────────────────────────────
      const positions = [
        { x: '-35%', y: '-28%', rotation: -12 },
        { x: '30%',  y: '-24%', rotation:  8  },
        { x: '-10%', y:  '32%', rotation: -5  },
      ]
      docRefs.current.forEach((el, i) => {
        if (!el) return
        gsap.set(el, { ...positions[i], opacity: 0, scale: 0.8 })
      })
      radarRefs.current.forEach((el, i) => {
        if (!el) return
        gsap.set(el, { scale: 0, opacity: 0 })
      })
      gsap.set(eMarkRef.current, { scale: 0, opacity: 0, rotation: -90 })
      badgeRefs.current.forEach(el => el && gsap.set(el, { scale: 0, opacity: 0 }))
      gsap.set(scorecardRef.current, { y: 40, opacity: 0, scale: 0.9 })

      // ── Phase 1 (0–2s): Doc cards converge ─────────────────────
      tl.to(docRefs.current.filter(Boolean), {
        x: 0, y: 0, rotation: 0, scale: 1, opacity: 1,
        duration: 1.2, ease: 'power3.out', stagger: 0.15,
      })

      // ── Phase 2 (2–3.5s): Radar rings + E mark ─────────────────
      .to(docRefs.current.filter(Boolean), { opacity: 0, scale: 0.6, duration: 0.4 })
      .to(radarRefs.current.filter(Boolean), {
        scale: 1, opacity: 1, duration: 0.7, ease: 'back.out(1.4)', stagger: 0.12,
      }, '-=0.2')
      .to(eMarkRef.current, {
        scale: 1, opacity: 1, rotation: 0, duration: 0.6, ease: 'back.out(1.8)',
      }, '-=0.4')

      // ── Phase 3 (3.5–5.5s): Alpha badges spread ────────────────
      .to(radarRefs.current.filter(Boolean), { opacity: 0.25, scale: 0.85, duration: 0.4 }, '+=0.3')
      .to(badgeRefs.current.filter(Boolean), {
        scale: 1, opacity: 1, duration: 0.5, ease: 'back.out(1.6)', stagger: 0.08,
      })

      // ── Phase 4 (5.5–7s): Scorecard rises ──────────────────────
      .to([...badgeRefs.current.filter(Boolean), eMarkRef.current, ...radarRefs.current.filter(Boolean)], {
        opacity: 0, scale: 0.7, duration: 0.5, stagger: 0.04,
      }, '+=0.5')
      .to(scorecardRef.current, {
        y: 0, opacity: 1, scale: 1, duration: 0.8, ease: 'power3.out',
      }, '-=0.2')

      // ── Phase 5 (7–8s): Fade out → restart ────────────────────
      .to(scorecardRef.current, { opacity: 0, y: -20, duration: 0.5 }, '+=1.2')
      .call(() => {
        docRefs.current.forEach((el, i) => {
          if (!el) return
          gsap.set(el, { ...positions[i], opacity: 0, scale: 0.8 })
        })
        badgeRefs.current.forEach(el => el && gsap.set(el, { scale: 0, opacity: 0 }))
        gsap.set(scorecardRef.current, { y: 40, opacity: 0, scale: 0.9 })
      })
    }, containerRef)

    return () => ctx.revert()
  }, [])

  // Badge positions in a circle
  const badgeAngles = ALPHA_LABELS.map((_, i) => (i / ALPHA_LABELS.length) * Math.PI * 2 - Math.PI / 2)
  const R = 90

  return (
    <div
      ref={containerRef}
      className="hidden lg:flex flex-[0_0_55%] relative bg-erebus-bg overflow-hidden items-center justify-center"
    >
      {/* Background radial glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse 60% 50% at 50% 50%, rgba(201,168,76,0.05) 0%, transparent 70%)',
        }}
      />

      {/* EREBUS brand watermark */}
      <div className="absolute top-8 left-8">
        <div className="flex items-center gap-2">
          <div
            className="w-6 h-6 rounded-full flex items-center justify-center border border-erebus-gold/40 font-serif text-erebus-gold text-xs"
            style={{ background: 'var(--gold-dim)' }}
          >
            E
          </div>
          <span className="font-serif text-[15px] text-erebus-text-2">EREBUS</span>
        </div>
        <p className="text-[11px] font-mono text-erebus-text-3 mt-1">Intelligence Engine</p>
      </div>

      {/* Animation stage */}
      <div className="relative w-80 h-80 flex items-center justify-center">

        {/* Document cards */}
        {DOCS.map(({ Icon, label }, i) => (
          <div
            key={i}
            ref={el => { docRefs.current[i] = el }}
            className="absolute flex items-center gap-2.5 px-4 py-2.5 rounded-lg whitespace-nowrap"
            style={{ background: '#0F1117', border: '1px solid rgba(255,255,255,0.09)' }}
          >
            <Icon size={14} className="text-erebus-blue shrink-0" />
            <span className="text-[12px] font-mono text-erebus-text-2">{label}</span>
          </div>
        ))}

        {/* Radar rings */}
        {[80, 120, 160].map((r, i) => (
          <div
            key={i}
            ref={el => { radarRefs.current[i] = el }}
            className="absolute rounded-full"
            style={{
              width: r * 2, height: r * 2,
              border: `1px solid rgba(201,168,76,${0.25 - i * 0.07})`,
              marginLeft: -r, marginTop: -r,
            }}
          />
        ))}

        {/* E mark */}
        <div
          ref={eMarkRef}
          className="absolute w-16 h-16 rounded-full flex items-center justify-center z-10"
          style={{
            background: 'var(--gold-dim)',
            border: '2px solid rgba(201,168,76,0.5)',
            boxShadow: '0 0 30px rgba(201,168,76,0.2)',
          }}
        >
          <span className="font-serif text-erebus-gold text-2xl">E</span>
        </div>

        {/* Alpha badges */}
        {ALPHA_LABELS.map((label, i) => (
          <div
            key={i}
            ref={el => { badgeRefs.current[i] = el }}
            className="absolute flex flex-col items-center gap-0.5"
            style={{
              left: '50%',
              top:  '50%',
              transform: `translate(calc(-50% + ${Math.cos(badgeAngles[i]) * R}px), calc(-50% + ${Math.sin(badgeAngles[i]) * R}px))`,
            }}
          >
            <div
              className="w-9 h-9 rounded-lg flex items-center justify-center text-[11px] font-mono font-semibold"
              style={{
                background: `rgba(201,168,76,0.10)`,
                border:     `1px solid rgba(201,168,76,0.25)`,
                color:      '#C9A84C',
              }}
            >
              {ALPHA_VALUES[i]}
            </div>
            <span className="text-[9px] font-mono text-erebus-text-3 whitespace-nowrap">{label}</span>
          </div>
        ))}

        {/* Scorecard */}
        <div
          ref={scorecardRef}
          className="absolute w-64 rounded-xl overflow-hidden"
          style={{
            background: '#0F1117',
            border: '1px solid rgba(201,168,76,0.20)',
            boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
          }}
        >
          <div className="px-4 py-3 border-b flex items-center gap-2" style={{ borderColor: 'var(--border)' }}>
            <div className="w-2 h-2 rounded-full bg-erebus-green animate-[pulse-dot_2s_infinite]" />
            <span className="text-[11px] font-mono text-erebus-text-2">HDFCBANK · EREBUS Score</span>
          </div>
          <div className="px-4 py-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[32px] font-mono font-semibold text-erebus-amber">71</span>
              <span className="text-[11px] font-mono text-erebus-text-3">/100</span>
            </div>
            {['Growth', 'Margin', 'Risk'].map((d, i) => (
              <div key={d} className="flex items-center gap-2 mb-2">
                <span className="text-[10px] font-mono text-erebus-text-3 w-20">{d}</span>
                <div className="flex-1 h-1 rounded-full bg-white/[0.07] overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${[68, 58, 61][i]}%`,
                      background: ['#4A8FE7', '#E09A25', '#D95555'][i],
                    }}
                  />
                </div>
                <span className="text-[10px] font-mono text-erebus-text-3">{[68, 58, 61][i]}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom caption */}
      <div className="absolute bottom-8 left-0 right-0 text-center">
        <p className="text-[11px] font-mono text-erebus-text-3">
          Evidence-based · Source-grounded · Zero hallucination
        </p>
      </div>
    </div>
  )
}
