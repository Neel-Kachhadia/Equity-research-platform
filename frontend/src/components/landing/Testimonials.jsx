import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import ScrollTrigger from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const QUOTES = [
  { quote: 'Finally, I can justify saying no to Bloomberg.', name: 'Rahul Sharma', title: 'Senior Analyst', firm: 'MOTILAL OSWAL' },
  { quote: 'Three minutes from ticker to decision. That\'s EREBUS.', name: 'Priya Venkat', title: 'Portfolio Manager', firm: 'MIRAE ASSET' },
  { quote: 'The source citations alone made me trust it. No other tool does this.', name: 'Arjun Nair', title: 'Equity Research', firm: 'SBI SECURITIES' },
  { quote: 'We run it alongside our analyst team. Cuts research time by 60%.', name: 'Deepa Krishnan', title: 'CIO', firm: 'EDELWEISS MF' },
]

function Stars() {
  return (
    <div className="flex gap-1 mb-4">
      {Array(5).fill(0).map((_, i) => (
        <svg key={i} width="13" height="13" viewBox="0 0 24 24" fill="#C9A84C">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </svg>
      ))}
    </div>
  )
}

export default function Testimonials() {
  const sectionRef = useRef(null)
  const headerRef  = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      const cards = sectionRef.current.querySelectorAll('.testimonial-card')

      gsap.set(headerRef.current, { y: 30, opacity: 0 })
      gsap.set(cards, { y: 50, opacity: 0, scale: 0.96 })

      const tl = gsap.timeline({
        scrollTrigger: { trigger: sectionRef.current, start: 'top 72%', once: true },
      })

      tl.to(headerRef.current, { y: 0, opacity: 1, duration: 0.7, ease: 'power3.out' })
      tl.to(cards, {
        y: 0, opacity: 1, scale: 1,
        stagger: { each: 0.12, from: 'start' },
        duration: 0.65, ease: 'power3.out',
      }, '-=0.3')
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  return (
    <section ref={sectionRef} className="erebus-section bg-erebus-bg">
      <div ref={headerRef}>
        <p className="section-label text-center mb-4">Social Proof</p>
        <h2 className="font-dm-serif text-[clamp(1.8rem,4vw,3rem)] text-center mb-14"
            style={{ color: '#EEE9E0', letterSpacing: '-0.02em' }}>
          What analysts say.
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 max-w-4xl mx-auto">
        {QUOTES.map((q, i) => (
          <div key={i} className="testimonial-card erebus-card gold-left-border pl-6">
            <Stars />
            <blockquote
              className="font-dm-serif italic text-[1.1rem] leading-[1.65] mb-5"
              style={{ color: '#EEE9E0' }}
            >
              &ldquo;{q.quote}&rdquo;
            </blockquote>
            <div>
              <p className="text-[14px] font-medium" style={{ color: '#EEE9E0' }}>{q.name}</p>
              <p className="font-jetbrains text-[11px] mt-0.5" style={{ color: '#8A8D9A' }}>
                {q.title} · <span style={{ color: '#C9A84C' }}>{q.firm}</span>
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
