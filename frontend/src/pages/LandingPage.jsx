/**
 * LandingPage.jsx — EREBUS Cinematic 3D Landing
 *
 * Structure:
 *  - Fixed Three.js canvas (z:0) — always fills viewport
 *  - Scroll container (650vh, z:1) — drives camera via ScrollTrigger
 *    ↳ Phase 1 (0-100vh):  Hero overlay
 *    ↳ Phase 2 (100-260vh): System viz overlay
 *    ↳ Phase 3 (260-400vh): Pipeline / Features overlay
 *    ↳ Phase 4 (400-520vh): Card gallery overlay
 *    ↳ Phase 5 (520-650vh): Final CTA
 *  - Normal HTML sections below fold: Pricing, Footer
 *
 * Key: All overlays use pointer-events:none except interactive elements.
 * Three.js scene is always active (fixed canvas).
 */

import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import gsap from 'gsap'
import ScrollTrigger from 'gsap/ScrollTrigger'
import { ErebusScene } from '../three/ErebusScene'
import Footer from '../components/landing/Footer'

gsap.registerPlugin(ScrollTrigger)

// ─── Grain overlay (renders as fixed SVG noise) ──────────────────
function GrainOverlay() {
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 5,
      pointerEvents: 'none',
      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.80' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='0.06'/%3E%3C/svg%3E")`,
      backgroundRepeat: 'repeat',
      backgroundSize: '200px 200px',
      mixBlendMode: 'overlay',
      opacity: 0.85,
    }} />
  )
}

// ─── Minimal navbar ───────────────────────────────────────────────
function CinematicNav({ scrolled, onNav }) {
  const NAV = [
    { label: 'System',  target: 'section-system'   },
    { label: 'Models',  target: 'section-pipeline'  },
    { label: 'Pricing', target: 'section-pricing'   },
  ]

  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50,
      padding: '1.2rem 2.5rem',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      background: scrolled ? 'rgba(9,9,15,0.75)' : 'transparent',
      backdropFilter: scrolled ? 'blur(18px)' : 'none',
      borderBottom: scrolled ? '1px solid rgba(201,168,76,0.08)' : 'none',
      transition: 'all 0.4s ease',
    }}>
      {/* Logo — click scrolls to top */}
      <div
        onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
      >
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          border: '1.5px solid rgba(201,168,76,0.6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ fontFamily: 'DM Serif Display, serif', color: '#C9A84C', fontSize: '14px', fontWeight: 700 }}>E</span>
        </div>
        <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '12px', letterSpacing: '0.12em', color: '#C9A84C' }}>EREBUS</span>
      </div>

      {/* Nav items */}
      <div style={{ display: 'flex', gap: '2.5rem', alignItems: 'center' }}>
        {NAV.map(({ label, target }) => (
          <button
            key={label}
            onClick={() => onNav(target)}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              fontFamily: 'JetBrains Mono, monospace', fontSize: '11px',
              letterSpacing: '0.1em', color: 'rgba(255,255,255,0.45)',
              transition: 'color 0.2s', textTransform: 'uppercase',
            }}
            onMouseEnter={e => e.currentTarget.style.color = '#C9A84C'}
            onMouseLeave={e => e.currentTarget.style.color = 'rgba(255,255,255,0.45)'}
          >
            {label}
          </button>
        ))}
        <Link
          to="/login"
          style={{
            fontFamily: 'JetBrains Mono, monospace', fontSize: '11px',
            letterSpacing: '0.1em', color: 'rgba(255,255,255,0.55)',
            textTransform: 'uppercase', padding: '7px 16px',
            border: '1px solid rgba(255,255,255,0.14)',
            borderRadius: '4px', transition: 'all 0.2s',
            textDecoration: 'none',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.color = '#C9A84C'
            e.currentTarget.style.borderColor = 'rgba(201,168,76,0.5)'
          }}
          onMouseLeave={e => {
            e.currentTarget.style.color = 'rgba(255,255,255,0.55)'
            e.currentTarget.style.borderColor = 'rgba(255,255,255,0.14)'
          }}
        >
          Log in
        </Link>
        <Link
          to="/signup"
          style={{
            fontFamily: 'JetBrains Mono, monospace', fontSize: '11px',
            letterSpacing: '0.1em', color: '#09090f',
            textTransform: 'uppercase', padding: '7px 18px',
            background: '#C9A84C', borderRadius: '4px',
            border: '1px solid #C9A84C',
            transition: 'all 0.2s', textDecoration: 'none',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = '#DFC06A'
            e.currentTarget.style.borderColor = '#DFC06A'
            e.currentTarget.style.boxShadow = '0 4px 20px rgba(201,168,76,0.35)'
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = '#C9A84C'
            e.currentTarget.style.borderColor = '#C9A84C'
            e.currentTarget.style.boxShadow = 'none'
          }}
        >
          Sign up
        </Link>
      </div>
    </nav>
  )
}

// ─── Phase overlays ───────────────────────────────────────────────

function HeroOverlay() {
  const lineRef  = useRef(null)
  const h1Ref    = useRef(null)
  const tagRef   = useRef(null)
  const ctaRef   = useRef(null)
  const subRef   = useRef(null)

  useEffect(() => {
    const tl = gsap.timeline({ delay: 0.6 })
    gsap.set([lineRef.current, tagRef.current, subRef.current, ctaRef.current], { opacity: 0 })
    gsap.set(h1Ref.current, { opacity: 0, y: 40 })

    tl.to(tagRef.current,   { opacity: 1, duration: 0.6, ease: 'power2.out' })
    tl.to(h1Ref.current,    { opacity: 1, y: 0, duration: 1.1, ease: 'expo.out' }, '-=0.2')
    tl.to(lineRef.current,  { opacity: 1, scaleX: 1, duration: 0.8, ease: 'expo.out', transformOrigin: 'left' }, '-=0.6')
    tl.to(subRef.current,   { opacity: 1, duration: 0.7, ease: 'power2.out' }, '-=0.3')
    tl.to(ctaRef.current,   { opacity: 1, y: 0, duration: 0.6, ease: 'power2.out' }, '-=0.3')
  }, [])

  return (
    <div style={{
      position: 'absolute', inset: 0,
      display: 'flex', alignItems: 'flex-end',
      padding: '0 6vw 7vh',
      pointerEvents: 'none',
    }}>
      {/* Main editorial block — bottom left, max 46% width so right side is exposed */}
      <div style={{ maxWidth: 'min(560px, 46vw)' }}>

        {/* Tag — top of block */}
        <div ref={tagRef} style={{
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: '11px', letterSpacing: '0.14em',
          color: '#C9A84C', marginBottom: '1.8rem',
          display: 'flex', alignItems: 'center', gap: '12px',
          opacity: 0,
        }}>
          
        </div>

        {/* Gold line accent */}
        <div ref={lineRef} style={{
          width: '48px', height: '2px', marginBottom: '1.6rem',
          background: 'linear-gradient(90deg, #C9A84C, #DFC06A)',
          opacity: 0, transform: 'scaleX(0)', transformOrigin: 'left',
        }} />

        {/* Headline — intentionally offset, not centered */}
        <h1 ref={h1Ref} style={{
          fontFamily: 'DM Serif Display, Georgia, serif',
          fontSize: 'clamp(3.2rem, 8vw, 7rem)',
          lineHeight: 1.0,
          letterSpacing: '-0.03em',
          color: '#EEE9E0',
          marginBottom: '2rem',
          opacity: 0,
        }}>
          The Intelligence<br />
          <em style={{
            background: 'linear-gradient(135deg, #DFC06A 0%, #F0D080 35%, #C9A84C 100%)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text',
          }}>
            Infrastructure.
          </em>
        </h1>

        {/* Subtitle — short, punchy */}
        <p ref={subRef} style={{
          fontFamily: 'Inter, sans-serif',
          fontSize: 'clamp(0.95rem, 1.4vw, 1.15rem)',
          lineHeight: 1.75,
          color: 'rgba(200,200,210,0.55)',
          maxWidth: '440px',
          marginBottom: '2.5rem',
          opacity: 0,
        }}>
          Reasoning across filings, transcripts, and structured data
          to produce analyst-grade intelligence — with zero hallucination.
        </p>

        {/* CTAs — pointer events re-enabled */}
        <div ref={ctaRef} style={{
          display: 'flex', gap: '16px', alignItems: 'center',
          pointerEvents: 'auto', opacity: 0,
        }}>
          <Link to="/app" style={{
            padding: '13px 28px', borderRadius: '6px',
            background: '#C9A84C', color: '#09090f',
            fontFamily: 'Inter, sans-serif', fontWeight: 700,
            fontSize: '14px', letterSpacing: '0.02em',
            boxShadow: '0 8px 32px rgba(201,168,76,0.3)',
            transition: 'all 0.2s',
          }}>
            Start analysing →
          </Link>
          <span style={{
            fontFamily: 'JetBrains Mono, monospace', fontSize: '11px',
            color: 'rgba(255,255,255,0.3)', letterSpacing: '0.08em',
          }}>
            NSE · BSE · SEBI · No credit card
          </span>
        </div>
      </div>

      {/* Top-right info block (asymmetric) */}
      <div style={{
        position: 'absolute', top: '12vh', right: '6vw',
        textAlign: 'right',
      }}>
        <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: 'rgba(255,255,255,0.18)', letterSpacing: '0.1em', marginBottom: '8px' }}>
          SCROLL TO NAVIGATE
        </div>
        <div style={{ width: '1px', height: '60px', background: 'linear-gradient(to bottom, rgba(201,168,76,0.35), transparent)', marginLeft: 'auto' }} />
      </div>

      {/* Bottom-right micro coordinate display */}
      <div style={{
        position: 'absolute', bottom: '6vh', right: '6vw',
        fontFamily: 'JetBrains Mono, monospace', fontSize: '9px',
        color: 'rgba(255,255,255,0.12)', letterSpacing: '0.08em',
        lineHeight: 1.8, textAlign: 'right',
      }}>
        <div>X: 000.000</div>
        <div>Y: 000.000</div>
        <div style={{ color: 'rgba(201,168,76,0.25)' }}>Z: 060.000</div>
      </div>

      {/* Left side thin vertical scan accent */}
      <div style={{
        position: 'absolute', left: '3vw', top: '15vh', bottom: '15vh',
        width: '1px',
        background: 'linear-gradient(to bottom, transparent, rgba(201,168,76,0.18) 30%, rgba(201,168,76,0.12) 70%, transparent)',
      }} />
    </div>
  )
}

function SystemOverlay() {
  const MODULES = [
    { label: 'RAG ENGINE',   desc: 'Retrieval-augmented generation grounded to source documents',  color: '#C9A84C' },
    { label: 'NLP PROCESSOR', desc: 'Semantic parsing of earnings transcripts and annual reports', color: '#4A8FE7' },
    { label: 'VECTOR STORE',  desc: 'Dense index of 10,000+ documents — sub-100ms recall',         color: '#2ECC8A' },
    { label: 'QUANT ENGINE',  desc: 'Structured financial metric extraction and normalisation',     color: '#E09A25' },
    { label: 'RISK ANALYSER', desc: 'Multi-factor risk signal scoring with confidence bounds',      color: '#D95555' },
    { label: 'SCORE ENGINE',  desc: '8-signal composite with evidence-linked output',               color: '#DFC06A' },
  ]
  const sRef = useRef(null)

  useEffect(() => {
    const el = sRef.current
    if (!el) return
    const items = el.querySelectorAll('.mod-item')
    gsap.set(items, { x: -30, opacity: 0 })
    ScrollTrigger.create({
      trigger: el,
      start: 'top 80%',
      once: true,
      onEnter() {
        gsap.to(items, { x: 0, opacity: 1, stagger: 0.07, duration: 0.7, ease: 'power3.out' })
      },
    })
    return () => ScrollTrigger.getAll().filter(t => t.vars?.trigger === el).forEach(t => t.kill())
  }, [])

  return (
    <div style={{
      position: 'sticky', top: 0, height: '100vh',
      display: 'flex', alignItems: 'center',
      padding: '0 6vw', pointerEvents: 'none',
    }}>
      {/* Left panel */}
      <div ref={sRef} style={{ maxWidth: '380px' }}>
        <p style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: '#C9A84C', letterSpacing: '0.14em', marginBottom: '1.2rem' }}>
          SYSTEM ARCHITECTURE
        </p>
        <h2 style={{
          fontFamily: 'DM Serif Display, serif',
          fontSize: 'clamp(2rem, 4vw, 3.2rem)',
          color: '#EEE9E0', lineHeight: 1.1,
          letterSpacing: '-0.02em', marginBottom: '2.5rem',
        }}>
          Six modules.<br /><em style={{ color: '#C9A84C' }}>One intelligence.</em>
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {MODULES.map(m => (
            <div key={m.label} className="mod-item" style={{ display: 'flex', gap: '14px', alignItems: 'flex-start', opacity: 0 }}>
              <div style={{ width: '3px', height: '36px', background: m.color, borderRadius: '2px', flexShrink: 0, marginTop: '4px' }} />
              <div>
                <p style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: m.color, letterSpacing: '0.1em', marginBottom: '3px' }}>{m.label}</p>
                <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', color: 'rgba(200,205,215,0.55)', lineHeight: 1.55 }}>{m.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function PipelineOverlay() {
  const ref = useRef(null)
  const STAGES = ['Ingest', 'Parse', 'Embed', 'Reason', 'Score', 'Cite']

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const items = el.querySelectorAll('.stage')
    gsap.set(items, { y: 20, opacity: 0 })
    ScrollTrigger.create({
      trigger: el, start: 'top 75%', once: true,
      onEnter() {
        gsap.to(items, { y: 0, opacity: 1, stagger: 0.12, duration: 0.7, ease: 'power2.out' })
      },
    })
  }, [])

  return (
    <div style={{
      position: 'sticky', top: 0, height: '100vh',
      display: 'flex', alignItems: 'center',
      justifyContent: 'flex-end',
      padding: '0 6vw', pointerEvents: 'none',
    }}>
      <div ref={ref} style={{ textAlign: 'right', maxWidth: '400px' }}>
        <p style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: '#4A8FE7', letterSpacing: '0.14em', marginBottom: '1.2rem' }}>
          DATA PIPELINE
        </p>
        <h2 style={{
          fontFamily: 'DM Serif Display, serif',
          fontSize: 'clamp(2rem, 4vw, 3.2rem)',
          color: '#EEE9E0', lineHeight: 1.1,
          letterSpacing: '-0.02em', marginBottom: '2.5rem',
        }}>
          Data flows in.<br /><em style={{ color: '#4A8FE7' }}>Knowledge emerges.</em>
        </h2>

        {/* Stage pills */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'flex-end' }}>
          {STAGES.map((s, i) => (
            <span key={s} className="stage" style={{
              fontFamily: 'JetBrains Mono, monospace', fontSize: '11px',
              padding: '6px 16px', borderRadius: '3px',
              background: 'rgba(74,143,231,0.10)',
              border: '1px solid rgba(74,143,231,0.28)',
              color: '#4A8FE7', letterSpacing: '0.08em',
              opacity: 0,
            }}>
              {String(i + 1).padStart(2, '0')} {s}
            </span>
          ))}
        </div>

        <p style={{
          marginTop: '2rem',
          fontFamily: 'Inter, sans-serif', fontSize: '14px',
          color: 'rgba(200,205,215,0.5)', lineHeight: 1.7,
        }}>
          From raw filing to scored analysis in under 4 seconds.<br />
          Every output grounded to a source document and page.
        </p>
      </div>
    </div>
  )
}

function FeaturesOverlay() {
  const FEATS = [
    { num: '01', label: 'Research Chat',    desc: 'Ask anything. Cited answers in seconds.',         color: '#C9A84C' },
    { num: '02', label: 'Company Scorecard', desc: '8-signal intelligence report from primary data.', color: '#4A8FE7' },
    { num: '03', label: 'Guidance Tracker', desc: 'Promised vs delivered — every quarter tracked.',   color: '#E09A25' },
    { num: '04', label: 'Peer Comparison',  desc: 'Up to 4 companies. Radar chart. AI summary.',      color: '#2ECC8A' },
    { num: '05', label: 'Document Upload',  desc: 'Any PDF or CSV. Indexed in 3 seconds.',           color: '#DFC06A' },
  ]
  const ref = useRef(null)

  useEffect(() => {
    const items = ref.current?.querySelectorAll('.feat-item')
    if (!items?.length) return
    gsap.set(items, { x: 30, opacity: 0 })
    ScrollTrigger.create({
      trigger: ref.current, start: 'top 75%', once: true,
      onEnter() { gsap.to(items, { x: 0, opacity: 1, stagger: 0.1, duration: 0.65, ease: 'power2.out' }) },
    })
  }, [])

  return (
    <div style={{
      position: 'sticky', top: 0, height: '100vh',
      display: 'flex', alignItems: 'center',
      padding: '0 6vw', pointerEvents: 'none',
    }}>
      <div ref={ref} style={{ maxWidth: '400px' }}>
        <p style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: '#DFC06A', letterSpacing: '0.14em', marginBottom: '1.2rem' }}>
          CAPABILITIES
        </p>
        <h2 style={{
          fontFamily: 'DM Serif Display, serif',
          fontSize: 'clamp(2rem, 3.5vw, 2.8rem)',
          color: '#EEE9E0', lineHeight: 1.15,
          letterSpacing: '-0.02em', marginBottom: '2.5rem',
        }}>
          Five workflows.<br /><em style={{ color: '#DFC06A' }}>Zero friction.</em>
        </h2>

        {FEATS.map(f => (
          <div key={f.num} className="feat-item" style={{
            display: 'flex', gap: '16px', marginBottom: '18px',
            paddingBottom: '18px', borderBottom: '1px solid rgba(255,255,255,0.05)',
            opacity: 0,
          }}>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '11px', color: f.color, flexShrink: 0, paddingTop: '2px' }}>
              {f.num}
            </span>
            <div>
              <p style={{ fontFamily: 'Inter, sans-serif', fontWeight: 600, fontSize: '13px', color: '#EEE9E0', marginBottom: '3px' }}>{f.label}</p>
              <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', color: 'rgba(200,205,215,0.5)', lineHeight: 1.55 }}>{f.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function CTAOverlay() {
  const ref = useRef(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    gsap.set(el, { opacity: 0, y: 30 })
    ScrollTrigger.create({
      trigger: el, start: 'top 80%', once: true,
      onEnter() { gsap.to(el, { opacity: 1, y: 0, duration: 1.0, ease: 'expo.out' }) },
    })
  }, [])

  return (
    <div style={{
      position: 'sticky', top: 0, height: '100vh',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      pointerEvents: 'none',
    }}>
      <div ref={ref} style={{ textAlign: 'center', opacity: 0 }}>
        {/* Gold horizontal line */}
        <div style={{
          width: '60px', height: '1px', margin: '0 auto 2rem',
          background: 'linear-gradient(90deg, transparent, #C9A84C, transparent)',
        }} />

        <p style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: '#C9A84C', letterSpacing: '0.16em', marginBottom: '1.5rem' }}>
          BEGIN
        </p>

        <h2 style={{
          fontFamily: 'DM Serif Display, serif',
          fontSize: 'clamp(3rem, 7vw, 6rem)',
          color: '#EEE9E0', lineHeight: 1.0,
          letterSpacing: '-0.03em', marginBottom: '1rem',
        }}>
          Your research.
        </h2>
        <h2 style={{
          fontFamily: 'DM Serif Display, serif',
          fontSize: 'clamp(3rem, 7vw, 6rem)',
          lineHeight: 1.0, letterSpacing: '-0.03em',
          marginBottom: '3rem',
          background: 'linear-gradient(135deg, #DFC06A 0%, #F0D080 40%, #C9A84C 100%)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text',
        }}>
          Amplified.
        </h2>

        <div style={{ pointerEvents: 'auto', display: 'flex', gap: '16px', justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link to="/signup" style={{
            padding: '16px 40px', borderRadius: '6px',
            background: '#C9A84C', color: '#09090f',
            fontFamily: 'Inter, sans-serif', fontWeight: 700, fontSize: '15px',
            boxShadow: '0 12px 40px rgba(201,168,76,0.35)',
            transition: 'all 0.2s',
          }}>
            Start free — no credit card
          </Link>
          <Link to="/login" style={{
            padding: '16px 32px', borderRadius: '6px',
            border: '1px solid rgba(201,168,76,0.35)',
            color: '#C9A84C', fontFamily: 'Inter, sans-serif', fontSize: '15px',
            background: 'rgba(201,168,76,0.04)',
            transition: 'all 0.2s',
          }}>
            Sign in →
          </Link>
        </div>

        <p style={{ marginTop: '1.5rem', fontFamily: 'JetBrains Mono, monospace', fontSize: '11px', color: 'rgba(255,255,255,0.2)', letterSpacing: '0.06em' }}>
          2,000+ analysts · NSE · BSE · SEBI-registered data
        </p>
      </div>
    </div>
  )
}

// ─── PRICING (below 3D scroll zone, normal HTML) ─────────────────
function PricingSection() {
  const TIERS = [
    {
      name: 'Scout', price: '₹0', per: '/mo',
      desc: 'For analysts exploring AI research.',
      cta: 'Start free', to: '/signup', featured: false,
      features: ['50 queries/month', 'Nifty 100 coverage', 'Basic scorecard', '3 document uploads'],
    },
    {
      name: 'Analyst', price: '₹2,999', per: '/mo',
      desc: 'Full access for serious buy-side and sell-side analysts.',
      cta: '30-day trial', to: '/signup', featured: true,
      features: ['Unlimited queries', 'Nifty 500+ coverage', '8-signal scorecard', 'Guidance tracker', 'Peer comparison (4)', '50 doc uploads/mo'],
    },
    {
      name: 'Quant', price: '₹9,999', per: '/mo',
      desc: 'API access and bulk data for quantitative teams.',
      cta: 'Contact sales', to: '#', featured: false,
      features: ['All Analyst features', 'REST + WebSocket API', 'Bulk CSV export', 'All-exchange coverage', 'Dedicated infra', '24/7 SLA'],
    },
  ]

  return (
    <section style={{ background: 'rgba(9,9,15,0.97)', padding: '7rem 5vw', borderTop: '1px solid rgba(201,168,76,0.12)' }}>
      <p style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: '#C9A84C', letterSpacing: '0.14em', textAlign: 'center', marginBottom: '1rem' }}>PRICING</p>
      <h2 style={{ fontFamily: 'DM Serif Display, serif', fontSize: 'clamp(2rem, 4vw, 3rem)', color: '#EEE9E0', textAlign: 'center', letterSpacing: '-0.02em', marginBottom: '4rem' }}>
        Transparent tiers.
      </h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px', maxWidth: '960px', margin: '0 auto' }}>
        {TIERS.map(t => (
          <div key={t.name} style={{
            borderRadius: '12px', padding: '2rem',
            background: t.featured ? 'rgba(201,168,76,0.04)' : 'rgba(255,255,255,0.02)',
            border: `1px solid ${t.featured ? 'rgba(201,168,76,0.35)' : 'rgba(255,255,255,0.08)'}`,
            boxShadow: t.featured ? '0 0 50px rgba(201,168,76,0.07)' : 'none',
          }}>
            {t.featured && <p style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: '#C9A84C', letterSpacing: '0.1em', marginBottom: '1rem' }}>MOST POPULAR</p>}
            <p style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '11px', color: '#8A8D9A', letterSpacing: '0.08em', marginBottom: '0.5rem' }}>{t.name.toUpperCase()}</p>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginBottom: '0.5rem' }}>
              <span style={{ fontFamily: 'DM Serif Display, serif', fontSize: '2.8rem', color: t.featured ? '#C9A84C' : '#EEE9E0' }}>{t.price}</span>
              <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '12px', color: '#4E5262' }}>{t.per}</span>
            </div>
            <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', color: '#8A8D9A', lineHeight: 1.6, marginBottom: '1.5rem' }}>{t.desc}</p>
            <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 1.5rem', display: 'flex', flexDirection: 'column', gap: '9px' }}>
              {t.features.map(f => (
                <li key={f} style={{ display: 'flex', gap: '10px', fontFamily: 'Inter, sans-serif', fontSize: '13px' }}>
                  <span style={{ color: '#2ECC8A', flexShrink: 0 }}>✓</span>
                  <span style={{ color: '#8A8D9A' }}>{f}</span>
                </li>
              ))}
            </ul>
            <Link to={t.to} style={{
              display: 'block', textAlign: 'center',
              padding: '12px', borderRadius: '6px',
              background: t.featured ? '#C9A84C' : 'transparent',
              border: t.featured ? 'none' : '1px solid rgba(201,168,76,0.3)',
              color: t.featured ? '#09090f' : '#C9A84C',
              fontFamily: 'Inter, sans-serif', fontWeight: t.featured ? 700 : 500,
              fontSize: '14px', transition: 'all 0.2s',
            }}>
              {t.cta}
            </Link>
          </div>
        ))}
      </div>
    </section>
  )
}

// ─── MAIN COMPONENT ───────────────────────────────────────────────

const SCROLL_HEIGHT = 650 // total 3D scroll in vh

export default function LandingPage() {
  const canvasRef   = useRef(null)
  const scrollRef   = useRef(null)
  const sceneRef    = useRef(null)
  const [scrolled, setScrolled] = useState(false)

  // Smooth scroll to a section by ID
  const scrollToSection = (id) => {
    const el = document.getElementById(id)
    if (!el) return
    const top = el.getBoundingClientRect().top + window.scrollY
    window.scrollTo({ top, behavior: 'smooth' })
  }

  useEffect(() => {
    // Init Three.js scene
    const scene = new ErebusScene(canvasRef.current)
    sceneRef.current = scene

    // Scroll → camera path
    const st = ScrollTrigger.create({
      trigger: scrollRef.current,
      start: 'top top',
      end: 'bottom bottom',
      scrub: 1.2,
      onUpdate(self) {
        scene.updateScroll(self.progress)
      },
    })

    // Navbar scroll style
    const onScroll = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', onScroll)

    return () => {
      scene.dispose()
      st.kill()
      window.removeEventListener('scroll', onScroll)
    }
  }, [])

  return (
    <div style={{ background: '#09090f', overflowX: 'hidden' }}>

      {/* ── Fixed Three.js canvas ─────────────────── */}
      <canvas
        ref={canvasRef}
        style={{
          position: 'fixed', inset: 0,
          width: '100%', height: '100%',
          zIndex: 0,
          display: 'block',
        }}
      />

      {/* ── Film grain overlay ────────────────────── */}
      <GrainOverlay />

      {/* ── Fixed navbar ─────────────────────────── */}
      <CinematicNav scrolled={scrolled} onNav={scrollToSection} />

      {/* ── Scroll container (650vh) ──────────────── */}
      {/* This div provides the scroll space for camera movement */}
      <div
        ref={scrollRef}
        style={{ position: 'relative', zIndex: 1, height: `${SCROLL_HEIGHT}vh` }}
      >
        {/* Phase 1 — HERO — 0-100vh */}
        <div style={{ position: 'relative', height: '100vh' }}>
          <HeroOverlay />
        </div>

        {/* Phase 2 — SYSTEM VIZ — 100-260vh (160vh, sticky for 100vh) */}
        <div id="section-system" style={{ position: 'relative', height: '160vh' }}>
          <SystemOverlay />
        </div>

        {/* Phase 3 — PIPELINE — 260-400vh */}
        <div id="section-pipeline" style={{ position: 'relative', height: '140vh' }}>
          <PipelineOverlay />
        </div>

        {/* Phase 4 — FEATURES — 400-520vh */}
        <div id="section-features" style={{ position: 'relative', height: '120vh' }}>
          <FeaturesOverlay />
        </div>

        {/* Phase 5 — CTA — 520-650vh */}
        <div style={{ position: 'relative', height: '130vh' }}>
          <CTAOverlay />
        </div>
      </div>

      {/* ── Below-fold: normal HTML sections ─────── */}
      {/* Camera has reached z=-55 by here; Three.js continues to animate */}
      <div style={{ position: 'relative', zIndex: 2, background: 'rgba(9,9,15,0.95)' }}>
        <div id="section-pricing">
          <PricingSection />
        </div>
        <Footer />
      </div>
    </div>
  )
}
