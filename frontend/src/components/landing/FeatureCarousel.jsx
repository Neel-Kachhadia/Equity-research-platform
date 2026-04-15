// FeatureCarousel.jsx — CSS sticky + GSAP scrub horizontal scroll
// Fix #1: Track is LEFT-ALIGNED (absolute inset-0 flex items-center) not flex-centered
// Fix #2: All cards fully vivid, active card gets gold glow + scale, inactive stays fully visible
import { useEffect, useRef, useState } from 'react'
import gsap from 'gsap'
import ScrollTrigger from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const SCENES = [
  {
    num: '01', tag: 'RESEARCH CHAT',
    title: 'Ask anything.\nGet cited answers.',
    desc: 'Natural language queries across 10,000+ documents. Every claim links to the exact source page.',
    chips: ['Zero hallucination', 'Source citations', 'Multi-doc reasoning'],
    accent: '#4A8FE7',
    lines: [
      { l: 'QUERY',  t: 'What drove NIM compression in Q4 FY24?',                      c: '#8A8D9A' },
      { l: 'ANSWER', t: 'NIM fell 28bps YoY to 3.63% — merger deposit repricing…',     c: '#EEE9E0' },
      { l: 'SOURCE', t: 'Annual Report FY24 · p.47',                                     c: '#4A8FE7' },
    ],
  },
  {
    num: '02', tag: 'COMPANY SCORECARD',
    title: 'One score.\nEight signals.',
    desc: 'Growth, Margin, Consistency, Risk, Volatility, Credibility, Sentiment — computed from primary data.',
    chips: ['8 alpha signals', 'Evidence-backed', 'Source-linked'],
    accent: '#2ECC8A',
    lines: [
      { l: 'SCORE',  t: '82 / 100 · Strong',       c: '#2ECC8A' },
      { l: 'GROWTH', t: '91 — Excellent',           c: '#2ECC8A' },
      { l: 'RISK',   t: '74 — Elevated caution',    c: '#E09A25' },
    ],
  },
  {
    num: '03', tag: 'GUIDANCE TRACKER',
    title: 'Hold management\naccountable.',
    desc: 'Quarter-by-quarter tracking of what was promised vs what was delivered.',
    chips: ['4-quarter history', 'Miss/beat flags', 'Credibility score'],
    accent: '#E09A25',
    lines: [
      { l: 'Q2 FY24', t: '12-14% guided → 11.2% actual',  c: '#D95555' },
      { l: 'Q3 FY24', t: '14-15% guided → 13.8% actual',  c: '#E09A25' },
      { l: 'Q4 FY24', t: '15-18% guided → 16.1% actual',  c: '#2ECC8A' },
    ],
  },
  {
    num: '04', tag: 'PEER COMPARISON',
    title: 'Rank within\nyour universe.',
    desc: 'Side-by-side analysis of up to 4 companies across any metric — radar chart + AI summary.',
    chips: ['Up to 4 companies', 'Radar chart', 'AI summary'],
    accent: '#C9A84C',
    lines: [
      { l: 'ICICIBANK',  t: 'Score 79 · ROE 18.4%', c: '#C9A84C' },
      { l: 'KOTAKBANK',  t: 'Score 76 · ROE 14.8%', c: '#C9A84C' },
      { l: 'HDFCBANK',   t: 'Score 71 · ROE 16.4%', c: '#C9A84C' },
    ],
  },
  {
    num: '05', tag: 'DOCUMENT UPLOAD',
    title: 'Bring your\nown files.',
    desc: 'Upload any PDF, CSV, or transcript. EREBUS indexes it instantly and reasons across it.',
    chips: ['PDF · CSV · TXT', '50MB per file', 'Instant indexing'],
    accent: '#2ECC8A',
    lines: [
      { l: 'UPLOAD', t: 'HDFC_Q4_Concall.pdf → indexed',     c: '#2ECC8A' },
      { l: 'UPLOAD', t: 'Balance_Sheet_FY24.xlsx → indexed',  c: '#2ECC8A' },
      { l: 'STATUS', t: 'Ready for queries in 3.2s',           c: '#8A8D9A' },
    ],
  },
]

function SceneCard({ scene, isActive }) {
  return (
    <div
      style={{
        background:    '#111318',
        border:        `1px solid ${isActive ? scene.accent : 'rgba(255,255,255,0.10)'}`,
        borderRadius:  '16px',
        padding:       '2.5rem',
        display:       'flex',
        flexDirection: 'column',
        gap:           '1.5rem',
        transform:     isActive ? 'scale(1) translateY(0)' : 'scale(0.96) translateY(8px)',
        boxShadow:     isActive
          ? `0 0 60px ${scene.accent}22, 0 20px 60px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06)`
          : '0 4px 24px rgba(0,0,0,0.4)',
        transition: 'transform 0.4s ease, box-shadow 0.4s ease, border-color 0.4s ease',
        maxWidth: '680px',
        width: '100%',
      }}
    >
      {/* Number + Tag row */}
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
        <span style={{
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: '5.5rem',
          fontWeight: 700,
          lineHeight: 1,
          color: isActive ? `${scene.accent}30` : 'rgba(255,255,255,0.06)',
          transition: 'color 0.4s ease',
        }}>
          {scene.num}
        </span>
        <span style={{
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: '11px',
          fontWeight: 600,
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: isActive ? scene.accent : '#4E5262',
          transition: 'color 0.4s ease',
        }}>
          {scene.tag}
        </span>
      </div>

      {/* Title */}
      <h3 style={{
        fontFamily: 'DM Serif Display, Georgia, serif',
        fontSize: 'clamp(1.6rem, 3vw, 2.1rem)',
        lineHeight: 1.2,
        color: '#EEE9E0',
        whiteSpace: 'pre-line',
        margin: 0,
      }}>
        {scene.title}
      </h3>

      {/* Description */}
      <p style={{
        fontSize: '15px',
        lineHeight: 1.75,
        color: '#9A9DAA',
        margin: 0,
      }}>
        {scene.desc}
      </p>

      {/* Chips */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        {scene.chips.map(c => (
          <span key={c} style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '12px',
            fontWeight: 500,
            padding: '5px 14px',
            borderRadius: '999px',
            background: isActive ? `${scene.accent}18` : 'rgba(255,255,255,0.05)',
            border:     `1px solid ${isActive ? `${scene.accent}40` : 'rgba(255,255,255,0.10)'}`,
            color:       isActive ? scene.accent : '#8A8D9A',
            transition: 'all 0.4s ease',
          }}>
            {c}
          </span>
        ))}
      </div>

      {/* Terminal preview */}
      <div style={{
        borderRadius: '12px',
        padding: '1.25rem 1.5rem',
        background: 'rgba(8,10,15,0.9)',
        border: `1px solid ${isActive ? `${scene.accent}20` : 'rgba(255,255,255,0.06)'}`,
        transition: 'border-color 0.4s ease',
      }}>
        {scene.lines.map((line, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '14px', marginBottom: i < scene.lines.length - 1 ? '12px' : 0 }}>
            <span style={{
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '10px',
              letterSpacing: '0.07em',
              textTransform: 'uppercase',
              color: '#4E5262',
              flexShrink: 0,
              paddingTop: '2px',
              width: '60px',
            }}>
              {line.l}
            </span>
            <span style={{
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '13px',
              lineHeight: 1.5,
              color: line.c,
            }}>
              {line.t}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function FeatureCarousel() {
  const outerRef  = useRef(null)   // tall section — provides scroll space
  const stickyRef = useRef(null)   // sticky 100vh viewport panel
  const trackRef  = useRef(null)   // translates left as outer scrolls
  const headerRef = useRef(null)
  const [active, setActive] = useState(0)

  useEffect(() => {
    const outer  = outerRef.current
    const sticky = stickyRef.current
    const track  = trackRef.current
    if (!outer || !sticky || !track) return

    const numScenes = SCENES.length

    const ctx = gsap.context(() => {
      // Header entrance
      gsap.set(headerRef.current, { y: 40, opacity: 0 })
      gsap.to(headerRef.current, {
        y: 0, opacity: 1, duration: 0.9, ease: 'power3.out',
        scrollTrigger: { trigger: outer, start: 'top 85%', once: true },
      })

      // Horizontal scroll — x goes from 0 → -(numScenes-1)*100vw
      // Use xPercent on the individual scene wrappers OR compute based on stickyRef width
      gsap.to(track, {
        x: () => -(numScenes - 1) * sticky.offsetWidth,
        ease: 'none',
        scrollTrigger: {
          trigger: outer,
          start: 'top top',
          end: 'bottom bottom',
          scrub: 0.5,
          invalidateOnRefresh: true,
          onUpdate(self) {
            const idx = Math.round(self.progress * (numScenes - 1))
            setActive(idx)
          },
        },
      })
    }, outer)

    return () => ctx.revert()
  }, [])

  return (
    <>
      {/* Section header — scrolls normally above the sticky carousel */}
      <div
        ref={headerRef}
        style={{ textAlign: 'center', padding: '5rem 2rem 3rem' }}
      >
        <p className="section-label" style={{ marginBottom: '1rem' }}>Feature Showcase</p>
        <h2
          className="font-dm-serif"
          style={{ fontSize: 'clamp(1.8rem, 4vw, 3rem)', color: '#EEE9E0', letterSpacing: '-0.02em', marginBottom: '1rem' }}
        >
          One platform. Five workflows.
        </h2>
        <p className="font-jetbrains" style={{ color: '#4E5262', fontSize: '13px', letterSpacing: '0.04em' }}>
          ↓ Scroll down to explore each capability
        </p>
      </div>

      {/* Tall outer section — 500vh total, gives scroll distance */}
      <section
        ref={outerRef}
        style={{ height: `${SCENES.length * 100}vh`, position: 'relative' }}
      >
        {/* Sticky panel — stays at top:0 while outer section scrolls */}
        <div
          ref={stickyRef}
          style={{
            position: 'sticky',
            top: 0,
            height: '100vh',
            overflow: 'hidden',
          }}
        >
          {/* Subtle radial glow */}
          <div style={{
            position: 'absolute', inset: 0, pointerEvents: 'none',
            background: `radial-gradient(ellipse 60% 60% at 50% 50%, ${SCENES[active]?.accent ?? '#C9A84C'}0A 0%, transparent 70%)`,
            transition: 'background 0.6s ease',
          }} />

          {/* Progress dots — top center */}
          <div style={{
            position: 'absolute', top: '24px', left: '50%',
            transform: 'translateX(-50%)',
            display: 'flex', alignItems: 'center', gap: '8px', zIndex: 10,
          }}>
            {SCENES.map((s, i) => (
              <div
                key={i}
                style={{
                  borderRadius: '999px',
                  height: '7px',
                  width:  i === active ? '28px' : '7px',
                  background: i === active ? s.accent : 'rgba(255,255,255,0.15)',
                  transition: 'all 0.35s ease',
                }}
              />
            ))}
          </div>

          {/* Scene counter — top right */}
          <div style={{ position: 'absolute', top: '24px', right: '32px', zIndex: 10 }}>
            <span style={{
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '12px',
              color: '#4E5262',
            }}>
              <span style={{ color: SCENES[active]?.accent ?? '#C9A84C' }}>
                {String(active + 1).padStart(2, '0')}
              </span>
              {' / '}
              {String(SCENES.length).padStart(2, '0')}
            </span>
          </div>

          {/* Track wrapper — IMPORTANT: absolute inset-0 so track left-edge = sticky left-edge */}
          <div style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',  /* vertically center the cards */
          }}>
            <div
              ref={trackRef}
              style={{
                display: 'flex',
                width: `${SCENES.length * 100}vw`,
                willChange: 'transform',
              }}
            >
              {SCENES.map((scene, idx) => (
                <div
                  key={scene.num}
                  style={{
                    flexShrink: 0,
                    width: '100vw',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '0 2rem',
                  }}
                >
                  <SceneCard scene={scene} isActive={idx === active} />
                </div>
              ))}
            </div>
          </div>

          {/* Bottom hint */}
          <div style={{
            position: 'absolute', bottom: '28px', left: '50%',
            transform: 'translateX(-50%)', zIndex: 10, textAlign: 'center',
          }}>
            <p style={{
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '11px',
              color: '#4E5262',
              letterSpacing: '0.05em',
            }}>
              {active < SCENES.length - 1 ? '↓ Keep scrolling' : 'Continue ↓'}
            </p>
          </div>
        </div>
      </section>
    </>
  )
}
