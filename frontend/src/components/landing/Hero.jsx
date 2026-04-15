import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import gsap from 'gsap'
import ScrollTrigger from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

// ── Particle canvas ─────────────────────────────────────────────────
function ParticleField() {
  const canvasRef = useRef(null)
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const resize = () => { canvas.width = canvas.offsetWidth; canvas.height = canvas.offsetHeight }
    resize()
    window.addEventListener('resize', resize)

    const particles = Array.from({ length: 48 }, () => ({
      x:  Math.random() * canvas.width,
      y:  Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
    }))

    let raf
    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      particles.forEach(p => {
        p.x += p.vx; p.y += p.vy
        if (p.x < 0 || p.x > canvas.width)  p.vx *= -1
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1
        ctx.beginPath()
        ctx.arc(p.x, p.y, 1.2, 0, Math.PI * 2)
        ctx.fillStyle = 'rgba(201,168,76,0.45)'
        ctx.fill()
      })
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x
          const dy = particles[i].y - particles[j].y
          const d  = Math.sqrt(dx * dx + dy * dy)
          if (d < 110) {
            ctx.beginPath()
            ctx.moveTo(particles[i].x, particles[i].y)
            ctx.lineTo(particles[j].x, particles[j].y)
            ctx.strokeStyle = `rgba(201,168,76,${0.12 * (1 - d / 110)})`
            ctx.lineWidth = 0.5
            ctx.stroke()
          }
        }
      }
      raf = requestAnimationFrame(draw)
    }
    draw()
    return () => { cancelAnimationFrame(raf); window.removeEventListener('resize', resize) }
  }, [])
  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />
}

// ── Split text into .erebus-char spans ────────────────────────────
// goldText: apply gradient directly to inner word span (background-clip:text needs to be on the element with the visible text)
function splitWords(text, goldText = false) {
  const goldStyle = goldText
    ? {
        background: 'linear-gradient(135deg, #DFC06A 0%, #F0D080 40%, #C9A84C 100%)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
      }
    : {}

  return text.split(' ').map((word, i, arr) => (
    <span key={i} className="erebus-char inline-block overflow-hidden" style={{ perspective: '800px' }}>
      <span
        className="inline-block"
        style={{ display: 'inline-block', ...goldStyle }}
        data-word
      >
        {word}{i < arr.length - 1 ? '\u00a0' : ''}
      </span>
    </span>
  ))
}

// ── Hero ─────────────────────────────────────────────────────────
export default function Hero() {
  const heroRef    = useRef(null)
  const titleRef   = useRef(null)
  const subRef     = useRef(null)
  const ctaRef     = useRef(null)
  const pillRef    = useRef(null)
  const chevronRef = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      const wordSpans = titleRef.current?.querySelectorAll('[data-word]') ?? []
      const subtitleEl = subRef.current
      const ctaEls = ctaRef.current?.children ?? []
      const pill = pillRef.current

      // Initial hidden state
      gsap.set(wordSpans,  { y: '110%', rotateX: -70, opacity: 0 })
      gsap.set(subtitleEl, { y: 24, opacity: 0 })
      gsap.set(Array.from(ctaEls), { y: 20, opacity: 0 })
      gsap.set(pill,       { y: -10, opacity: 0 })

      const tl = gsap.timeline({ delay: 0.1 })

      // Pill badge
      tl.to(pill, { y: 0, opacity: 1, duration: 0.5, ease: 'power2.out' })

      // Staggered word reveal
      tl.to(wordSpans, {
        y: '0%', rotateX: 0, opacity: 1,
        stagger: 0.07, duration: 0.85, ease: 'expo.out',
      }, '-=0.2')

      // Subtitle
      tl.to(subtitleEl, { y: 0, opacity: 1, duration: 0.75, ease: 'power3.out' }, '-=0.5')

      // CTAs
      tl.to(Array.from(ctaEls), { y: 0, opacity: 1, stagger: 0.1, duration: 0.65, ease: 'power2.out' }, '-=0.45')

      // Scroll parallax — title fades up as user scrolls
      ScrollTrigger.create({
        trigger: heroRef.current,
        start: 'top top',
        end: 'bottom top',
        scrub: true,
        onUpdate(self) {
          if (!titleRef.current) return
          gsap.set(titleRef.current, {
            y:       self.progress * 80,
            opacity: 1 - self.progress * 1.8,
          })
        },
      })

      // Chevron bounce
      if (chevronRef.current) {
        gsap.to(chevronRef.current, {
          y: 10, opacity: 0.35, duration: 0.85,
          repeat: -1, yoyo: true, ease: 'sine.inOut', delay: 2.5,
        })
      }
    }, heroRef)
    return () => ctx.revert()
  }, [])

  return (
    <section
      ref={heroRef}
      className="relative w-full min-h-screen flex flex-col items-center
                 justify-center overflow-hidden text-center px-6"
      style={{ background: 'transparent' }}
    >
      <ParticleField />

      {/* Radial gold atmosphere */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: 'radial-gradient(ellipse 80% 60% at 50% 50%, rgba(201,168,76,0.12) 0%, transparent 70%)' }}
      />

      {/* Content */}
      <div className="relative z-10 max-w-5xl w-full flex flex-col items-center">

        {/* Pill badge */}
        <div
          ref={pillRef}
          className="flex items-center gap-2 px-4 py-1.5 rounded-full text-[11px]
                     font-mono tracking-[0.12em] text-erebus-gold
                     mb-8"
          style={{ background: 'rgba(201,168,76,0.08)', border: '1px solid rgba(201,168,76,0.25)' }}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-erebus-gold inline-block" style={{ animation: 'pulse-dot 2s infinite' }} />
          SECTION ALPHA · EQUITY RESEARCH AI
        </div>

        {/* Headline — GSAP staggered word reveal */}
        <h1
          ref={titleRef}
          style={{ perspective: '1000px', willChange: 'transform' }}
          className="font-dm-serif leading-[1.1] mb-8"
        >
          <span className="block text-[clamp(2.6rem,7vw,5rem)] text-erebus-text-1 tracking-tight">
            {splitWords('The research layer')}
          </span>
          <span className="block text-[clamp(2.6rem,7vw,5rem)] italic tracking-tight">
            {splitWords('Indian equity deserves.', true)}
          </span>
        </h1>

        {/* Subtitle */}
        <p
          ref={subRef}
          className="text-[clamp(1rem,2vw,1.2rem)] leading-[1.8] max-w-[640px] mb-10"
          style={{ color: '#8A8D9A' }}
        >
          EREBUS ingests filings, transcripts, and structured data — then reasons
          across companies, time, and risk to produce analyst-grade intelligence
          with zero hallucination and full source citation.
        </p>

        {/* CTAs */}
        <div ref={ctaRef} className="flex gap-4 flex-wrap justify-center">
          <Link
            to="/app"
            className="cta-button-primary text-[15px] rounded-lg"
          >
            Start analysing free →
          </Link>
          <button className="cta-button-secondary text-[15px] rounded-lg">
            ▶ Watch 3-min demo
          </button>
        </div>

        {/* Trust line */}
        <p className="mt-8 text-[12px] font-mono tracking-[0.05em]" style={{ color: '#4E5262' }}>
          NSE · BSE · SEBI Filings · Earnings Transcripts · Annual Reports
        </p>
      </div>

      {/* Scroll chevron */}
      <div
        ref={chevronRef}
        className="absolute bottom-10 left-1/2 -translate-x-1/2 erebus-chevron"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 5v14M5 12l7 7 7-7" />
        </svg>
      </div>
    </section>
  )
}
