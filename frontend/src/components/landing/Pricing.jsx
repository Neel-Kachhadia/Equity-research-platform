import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import gsap from 'gsap'
import ScrollTrigger from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const TIERS = [
  {
    name: 'Scout', price: '₹0', per: '/month',
    desc: 'For analysts getting started with AI-assisted research.',
    cta: 'Start free', link: '/signup', featured: false,
    features: ['50 queries / month', 'Nifty 100 coverage', 'Basic scorecard', '3 document uploads', 'Community support'],
  },
  {
    name: 'Analyst', price: '₹2,999', per: '/month',
    desc: 'Full access for serious buy-side and sell-side analysts.',
    cta: 'Start 30-day trial', link: '/signup', featured: true,
    features: ['Unlimited queries', 'Nifty 500 + SME coverage', 'Full 8-signal scorecard', 'Guidance tracker', 'Peer comparison (4 companies)', '50 document uploads / month', 'Priority support'],
  },
  {
    name: 'Quant', price: '₹9,999', per: '/month',
    desc: 'API access and bulk data for quantitative research teams.',
    cta: 'Contact sales', link: '#', featured: false,
    features: ['Everything in Analyst', 'REST + WebSocket API', 'Bulk data export (CSV)', 'All-exchange coverage', 'Webhook alerts', 'Dedicated infrastructure', '24/7 SLA'],
  },
]

export default function Pricing() {
  const sectionRef = useRef(null)
  const headerRef  = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      const cards = sectionRef.current.querySelectorAll('.pricing-card')
      const featured = sectionRef.current.querySelector('.pricing-featured')

      gsap.set(headerRef.current, { y: 30, opacity: 0 })
      gsap.set(cards, { y: 60, opacity: 0, scale: 0.95 })

      const tl = gsap.timeline({
        scrollTrigger: { trigger: sectionRef.current, start: 'top 72%', once: true },
      })

      tl.to(headerRef.current, { y: 0, opacity: 1, duration: 0.7, ease: 'power3.out' })
      tl.to(cards, {
        y: 0, opacity: 1, scale: 1,
        stagger: 0.15, duration: 0.7, ease: 'power3.out',
      }, '-=0.3')

      // Featured card extra glow pulse on entrance
      if (featured) {
        tl.from(featured, {
          boxShadow: '0 0 0px rgba(201,168,76,0)',
          duration: 0.8, ease: 'power2.out',
        }, '<0.4')
      }
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  return (
    <section ref={sectionRef} className="erebus-section bg-erebus-bg">
      <div ref={headerRef}>
        <p className="section-label text-center mb-4">Pricing</p>
        <h2 className="font-dm-serif text-[clamp(1.8rem,4vw,3rem)] text-center mb-4"
            style={{ color: '#EEE9E0', letterSpacing: '-0.02em' }}>
          Transparent tiers.
        </h2>
        <p className="text-center text-[15px] mb-14 max-w-md mx-auto" style={{ color: '#8A8D9A' }}>
          Start free. Upgrade when you need more power.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 max-w-5xl mx-auto">
        {TIERS.map(tier => (
          <div
            key={tier.name}
            className={`pricing-card rounded-xl p-7 flex flex-col gap-5
              ${tier.featured ? 'pricing-featured erebus-card-featured' : 'erebus-card card-interactive'}`}
          >
            {tier.featured && (
              <div className="chip-gold text-[11px] px-3 py-1 rounded-full w-fit mx-auto text-center">
                MOST POPULAR
              </div>
            )}
            <div>
              <p className="erebus-label mb-2">{tier.name.toUpperCase()}</p>
              <div className="flex items-end gap-1">
                <span className="font-dm-serif text-[2.8rem] leading-none"
                      style={{ color: tier.featured ? '#C9A84C' : '#EEE9E0' }}>
                  {tier.price}
                </span>
                <span className="font-jetbrains text-[12px] mb-1.5" style={{ color: '#4E5262' }}>
                  {tier.per}
                </span>
              </div>
              <p className="text-[13px] mt-2 leading-[1.6]" style={{ color: '#8A8D9A' }}>
                {tier.desc}
              </p>
            </div>

            <ul className="flex-1 space-y-2.5">
              {tier.features.map(f => (
                <li key={f} className="flex items-start gap-2.5 text-[13px]">
                  <span style={{ color: '#2ECC8A', flexShrink: 0 }}>✓</span>
                  <span style={{ color: '#8A8D9A' }}>{f}</span>
                </li>
              ))}
            </ul>

            <Link
              to={tier.link}
              className={`text-center py-3 px-6 rounded-lg text-[14px] font-semibold block transition-all duration-150
                ${tier.featured ? 'cta-button-primary' : 'cta-button-secondary'}`}
            >
              {tier.cta}
            </Link>
          </div>
        ))}
      </div>
    </section>
  )
}
