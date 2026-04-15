import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import gsap from 'gsap'
import ScrollTrigger from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

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
    <span key={i} className="inline-block overflow-hidden">
      <span className="inline-block" style={goldStyle} data-cta-word>
        {word}{i < arr.length - 1 ? '\u00a0' : ''}
      </span>
    </span>
  ))
}

export default function FinalCTA() {
  const sectionRef = useRef(null)
  const lineRef    = useRef(null)
  const labelRef   = useRef(null)
  const ctaRef     = useRef(null)
  const subRef     = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      const words = sectionRef.current.querySelectorAll('[data-cta-word]')

      // Initial states
      gsap.set(lineRef.current,  { scaleX: 0, opacity: 0 })
      gsap.set(labelRef.current, { y: 20, opacity: 0 })
      gsap.set(words,            { y: '110%', opacity: 0 })
      gsap.set(subRef.current,   { y: 20, opacity: 0 })
      gsap.set(ctaRef.current,   { y: 20, opacity: 0, scale: 0.95 })

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 75%',
          once: true,
        },
      })

      tl.to(lineRef.current, {
        scaleX: 1, opacity: 1, duration: 0.9, ease: 'expo.out',
        transformOrigin: 'center',
      })
      tl.to(labelRef.current, { y: 0, opacity: 1, duration: 0.6, ease: 'power3.out' }, '-=0.4')
      tl.to(words, {
        y: '0%', opacity: 1,
        stagger: 0.06, duration: 0.8, ease: 'expo.out',
      }, '-=0.3')
      tl.to(subRef.current,  { y: 0, opacity: 1, duration: 0.6, ease: 'power3.out' }, '-=0.4')
      tl.to(ctaRef.current,  { y: 0, opacity: 1, scale: 1, duration: 0.6, ease: 'back.out(1.4)' }, '-=0.3')
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  return (
    <section
      ref={sectionRef}
      className="relative overflow-hidden text-center"
      style={{ padding: 'clamp(5rem,8vw,10rem) 2rem' }}
    >
      {/* Radial gold atmosphere */}
      <div className="absolute inset-0 pointer-events-none"
           style={{ background: 'radial-gradient(ellipse 80% 60% at 50% 50%, rgba(201,168,76,0.06) 0%, transparent 70%)' }} />

      {/* Gold line */}
      <div ref={lineRef} className="w-20 h-px mx-auto mb-12"
           style={{ background: 'linear-gradient(90deg, transparent, #C9A84C, transparent)', transformOrigin: 'center' }} />

      <div className="relative z-10 max-w-3xl mx-auto">
        <p ref={labelRef} className="section-label mb-6">Ready to begin?</p>

        <h2 className="font-dm-serif leading-[1.1] mb-6"
            style={{ fontSize: 'clamp(2.5rem,6vw,4.5rem)', letterSpacing: '-0.02em', color: '#EEE9E0' }}>
          <span className="block italic">
            {splitWords('Your research.')}
          </span>
          <span className="block">
            {splitWords('Amplified.', true)}
          </span>
        </h2>

        <p ref={subRef} className="text-[16px] mb-10 mx-auto max-w-[480px] leading-[1.8]"
           style={{ color: '#8A8D9A' }}>
          30-day free trial. No credit card. Cancel anytime.
        </p>

        <div ref={ctaRef}>
          <Link to="/signup"
                className="cta-button-primary text-[16px] rounded-xl inline-block px-10 py-4">
            Begin analysis →
          </Link>
          <p className="mt-5 font-jetbrains text-[11px] tracking-[0.06em]"
             style={{ color: '#4E5262' }}>
            Used by 2,000+ analysts · SEBI-registered data sources
          </p>
        </div>
      </div>
    </section>
  )
}
