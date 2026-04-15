import { useState, useEffect, useRef } from 'react'
import gsap from 'gsap'
import ScrollTrigger from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const FAQS = [
  {
    q: 'Do you really have India-focused financial data?',
    a: 'Yes. EREBUS is built specifically for Indian equity markets. We index NSE and BSE filings, SEBI regulatory disclosures, earnings call transcripts, and annual reports — going back 5 years across Nifty 500 companies.',
  },
  {
    q: 'How accurate is the AI scoring system?',
    a: 'Our internal benchmarks show 94.2% fact-check accuracy against primary source documents. Every claim is grounded to a specific page. We flag low-confidence answers and are transparent about model confidence levels.',
  },
  {
    q: 'Can I upload my own research documents?',
    a: 'Absolutely. EREBUS supports PDF, CSV, TXT, and DOCX uploads up to 50MB each. Uploaded files are indexed within seconds and immediately become queryable alongside our core corpus.',
  },
  {
    q: 'Is my research data private?',
    a: 'Yes. Your uploaded documents and query history are private to your account. We do not use your data to train shared models. Enterprise plans include dedicated infrastructure isolation.',
  },
  {
    q: 'Can I use EREBUS without coding?',
    a: 'Yes — the research interface is fully no-code. You type in natural language, EREBUS responds with analysis. The API access tier is available for quants who want programmatic access.',
  },
]

export default function FAQAccordion() {
  const [open, setOpen] = useState(null)
  const sectionRef = useRef(null)
  const headerRef  = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      const items = sectionRef.current.querySelectorAll('.faq-item')

      gsap.set(headerRef.current, { y: 30, opacity: 0 })
      gsap.set(items, { y: 30, opacity: 0 })

      const tl = gsap.timeline({
        scrollTrigger: { trigger: sectionRef.current, start: 'top 72%', once: true },
      })

      tl.to(headerRef.current, { y: 0, opacity: 1, duration: 0.7, ease: 'power3.out' })
      tl.to(items, { y: 0, opacity: 1, stagger: 0.08, duration: 0.6, ease: 'power3.out' }, '-=0.3')
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  return (
    <section ref={sectionRef} className="erebus-section">
      <div ref={headerRef}>
        <p className="section-label text-center mb-4">FAQ</p>
        <h2 className="font-dm-serif text-[clamp(1.8rem,4vw,3rem)] text-center mb-14"
            style={{ color: '#EEE9E0', letterSpacing: '-0.02em' }}>
          Common questions.
        </h2>
      </div>

      <div className="max-w-2xl mx-auto">
        {FAQS.map((item, i) => (
          <div
            key={i}
            className="faq-item"
            style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}
          >
            <button
              onClick={() => setOpen(open === i ? null : i)}
              className="w-full flex items-center justify-between gap-4 py-5 text-left group"
            >
              <span
                className="text-[15px] leading-[1.5] transition-colors duration-200"
                style={{ color: open === i ? '#EEE9E0' : '#8A8D9A' }}
              >
                {item.q}
              </span>
              <svg
                width="16" height="16" viewBox="0 0 24 24"
                fill="none" stroke="#C9A84C" strokeWidth="2" strokeLinecap="round"
                style={{
                  flexShrink: 0,
                  transform: open === i ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.3s ease',
                }}
              >
                <path d="M6 9l6 6 6-6" />
              </svg>
            </button>

            <div
              style={{
                maxHeight: open === i ? '300px' : '0',
                overflow: 'hidden',
                transition: 'max-height 0.35s ease',
              }}
            >
              <p className="pb-5 text-[14px] leading-[1.8]" style={{ color: '#8A8D9A' }}>
                {item.a}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
