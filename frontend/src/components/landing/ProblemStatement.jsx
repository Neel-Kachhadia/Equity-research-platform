import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import ScrollTrigger from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const PROBLEMS = [
  {
    tag:   'COST',
    title: 'Bloomberg is $24,000/year.',
    sub:   'Indian analysts deserve institutional-grade tools — not institutional price tags.',
    value: '₹24K', unit: '/year', accent: '#D95555',
  },
  {
    tag:   'DATA SILOS',
    title: 'Your data is scattered everywhere.',
    sub:   'Annual reports, concall transcripts, IR pages, SEBI filings — all unconnected.',
    value: '12+', unit: 'tabs', accent: '#8A8D9A',
  },
  {
    tag:   'SPEED',
    title: 'Analyst reports take 2 weeks.',
    sub:   'By the time your research is done, the market has already moved. EREBUS takes minutes.',
    value: '2wk→3m', unit: '', accent: '#2ECC8A',
  },
]

export default function ProblemStatement() {
  const sectionRef = useRef(null)
  const labelRef   = useRef(null)
  const headRef    = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      const cards = sectionRef.current.querySelectorAll('.problem-card')
      const nums  = sectionRef.current.querySelectorAll('.problem-num')

      // Initial state — must be within context
      gsap.set([labelRef.current, headRef.current], { y: 30, opacity: 0 })
      gsap.set(cards, { y: 60, opacity: 0 })
      gsap.set(nums,  { scale: 0.7, opacity: 0 })

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 75%',
          once: true,
        },
      })

      tl.to([labelRef.current, headRef.current], {
        y: 0, opacity: 1, stagger: 0.12, duration: 0.7, ease: 'power3.out',
      })
      tl.to(cards, {
        y: 0, opacity: 1, stagger: 0.15, duration: 0.7, ease: 'power3.out',
      }, '-=0.3')
      tl.to(nums, {
        scale: 1, opacity: 1, stagger: 0.15, duration: 0.5, ease: 'back.out(1.7)',
      }, '<0.1')
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  return (
    <section ref={sectionRef} className="erebus-section bg-erebus-bg">
      <p ref={labelRef} className="section-label text-center mb-4">The Problem</p>
      <h2
        ref={headRef}
        className="font-dm-serif text-[clamp(1.8rem,4vw,3rem)] text-center mb-14"
        style={{ color: '#EEE9E0', letterSpacing: '-0.02em' }}
      >
        Equity research is broken.
      </h2>

      <div className="erebus-3-column max-w-5xl mx-auto">
        {PROBLEMS.map(p => (
          <div key={p.tag} className="problem-card erebus-card gold-top-border">
            <div className="erebus-label mb-3">{p.tag}</div>
            <div
              className="problem-num font-jetbrains text-[2.6rem] font-bold leading-none mb-4"
              style={{ color: p.accent }}
            >
              {p.value}
              {p.unit && (
                <span className="text-[1rem] ml-1.5 opacity-60">{p.unit}</span>
              )}
            </div>
            <h3 className="font-dm-serif text-[1.2rem] mb-2" style={{ color: '#EEE9E0' }}>
              {p.title}
            </h3>
            <p className="text-[14px] leading-[1.7]" style={{ color: '#8A8D9A' }}>{p.sub}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
