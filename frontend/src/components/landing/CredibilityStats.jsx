import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import ScrollTrigger from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const STATS = [
  { id: 'stat-docs',     end: 10000, suffix: 'K+',  display: '10K+',   label: 'DOCUMENTS INDEXED',   desc: 'Annual reports, concall transcripts, SEBI filings — fully vectorised.' },
  { id: 'stat-accuracy', end: 94.2,  suffix: '%',   display: '94.2%',  label: 'FACT-CHECK RATE',      desc: 'Every response validated against primary sources. Independently benchmarked.' },
  { id: 'stat-analysts', end: 2000,  suffix: '+',   display: '2,000+', label: 'ANALYSTS SERVED',      desc: 'From retail investors to portfolio managers at top Indian asset managers.' },
]

export default function CredibilityStats() {
  const sectionRef = useRef(null)
  const labelRef   = useRef(null)
  const headRef    = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      const cards = sectionRef.current.querySelectorAll('.stat-card')
      const dividers = sectionRef.current.querySelectorAll('.stat-divider')

      // Initial states
      gsap.set([labelRef.current, headRef.current], { y: 30, opacity: 0 })
      gsap.set(cards, { y: 50, opacity: 0 })
      gsap.set(dividers, { scaleY: 0, opacity: 0 })

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 72%',
          once: true,
        },
      })

      tl.to([labelRef.current, headRef.current], {
        y: 0, opacity: 1, stagger: 0.1, duration: 0.7, ease: 'power3.out',
      })
      tl.to(dividers, {
        scaleY: 1, opacity: 1, stagger: 0.15, duration: 0.6, ease: 'power2.out',
      }, '-=0.3')
      tl.to(cards, {
        y: 0, opacity: 1, stagger: 0.12, duration: 0.65, ease: 'power3.out',
      }, '<')

      // Counter animations for each number
      STATS.forEach(stat => {
        const el = document.getElementById(stat.id)
        if (!el) return
        const obj = { val: 0 }
        gsap.to(obj, {
          val: stat.end,
          duration: 2.2,
          ease: 'power2.out',
          scrollTrigger: { trigger: sectionRef.current, start: 'top 72%', once: true },
          onUpdate() {
            const v = obj.val
            if (stat.suffix === 'K+') {
              el.textContent = v >= 1000
                ? (v / 1000).toFixed(0) + 'K+'
                : Math.round(v) + ''
            } else if (stat.suffix === '%') {
              el.textContent = v.toFixed(1) + '%'
            } else {
              el.textContent = Math.round(v).toLocaleString() + '+'
            }
          },
        })
      })
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  return (
    <section
      ref={sectionRef}
      className="erebus-section bg-erebus-surface"
      style={{ borderTop: '1px solid rgba(255,255,255,0.07)', borderBottom: '1px solid rgba(255,255,255,0.07)' }}
    >
      <div className="max-w-5xl mx-auto">
        <p ref={labelRef} className="section-label text-center mb-4">By the numbers</p>
        <h2
          ref={headRef}
          className="font-dm-serif text-[clamp(1.8rem,4vw,3rem)] text-center mb-16"
          style={{ color: '#EEE9E0', letterSpacing: '-0.02em' }}
        >
          Built for professionals.
        </h2>

        <div className="flex flex-col md:flex-row items-start justify-center divide-y md:divide-y-0 gap-0">
          {STATS.map((stat, i) => (
            <div key={stat.id} className="relative flex-1">
              {/* Vertical divider between columns */}
              {i > 0 && (
                <div
                  className="stat-divider hidden md:block absolute left-0 top-1/2 -translate-y-1/2"
                  style={{ width: '1px', height: '80px', background: 'rgba(255,255,255,0.07)', transformOrigin: 'top' }}
                />
              )}
              <div className="stat-card text-center px-8 py-8">
                {/* Animated counter */}
                <div
                  id={stat.id}
                  className="font-jetbrains font-bold leading-none mb-3 text-gradient-gold"
                  style={{ fontSize: 'clamp(2.8rem,5vw,4rem)' }}
                >
                  {stat.display}
                </div>
                <div className="erebus-label mb-3">{stat.label}</div>
                <p className="text-[14px] leading-[1.8] max-w-[240px] mx-auto" style={{ color: '#8A8D9A' }}>
                  {stat.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
