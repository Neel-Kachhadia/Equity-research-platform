import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import ScrollTrigger from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const ROWS = [
  { feature: 'India-focused corpus',   bloomberg: false, manual: false, erebus: true  },
  { feature: 'AI-assisted insights',   bloomberg: false, manual: false, erebus: true  },
  { feature: 'Source citations',        bloomberg: true,  manual: false, erebus: true  },
  { feature: 'Real-time scoring',       bloomberg: true,  manual: false, erebus: true  },
  { feature: 'Guidance tracker',        bloomberg: false, manual: false, erebus: true  },
  { feature: 'Natural language query',  bloomberg: false, manual: false, erebus: true  },
  { feature: 'Mobile-friendly',         bloomberg: false, manual: true,  erebus: true  },
  { feature: 'Monthly cost',
    bloombergVal: '₹1.7L+', manualVal: '₹0 (40 hrs/wk)', erebusVal: 'Free → ₹2,999' },
]

const Tick = ({ ok }) => ok
  ? <span className="text-[18px]" style={{ color: '#2ECC8A' }}>✓</span>
  : <span className="text-[16px]" style={{ color: '#4E5262' }}>—</span>

export default function ComparisonTable() {
  const sectionRef = useRef(null)
  const headerRef  = useRef(null)
  const tableRef   = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      const rows = tableRef.current?.querySelectorAll('tbody tr') ?? []

      gsap.set(headerRef.current, { y: 30, opacity: 0 })
      gsap.set(tableRef.current,  { y: 40, opacity: 0 })
      gsap.set(rows, { x: -20, opacity: 0 })

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 72%',
          once: true,
        },
      })

      tl.to(headerRef.current, { y: 0, opacity: 1, duration: 0.7, ease: 'power3.out' })
      tl.to(tableRef.current,  { y: 0, opacity: 1, duration: 0.6, ease: 'power3.out' }, '-=0.3')
      tl.to(rows, { x: 0, opacity: 1, stagger: 0.06, duration: 0.5, ease: 'power2.out' }, '-=0.4')
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  return (
    <section ref={sectionRef} className="erebus-section">
      <div ref={headerRef}>
        <p className="section-label text-center mb-4">Competitive Landscape</p>
        <h2 className="font-dm-serif text-[clamp(1.8rem,4vw,3rem)] text-center mb-14"
            style={{ color: '#EEE9E0', letterSpacing: '-0.02em' }}>
          Why EREBUS wins.
        </h2>
      </div>

      <div ref={tableRef} className="max-w-3xl mx-auto elevated rounded-xl overflow-hidden">
        <table className="w-full text-[14px]">
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.07)', background: '#0F1117' }}>
              <th className="px-6 py-4 text-left font-normal w-[40%]">
                <span className="font-jetbrains text-[10px] tracking-[0.1em]" style={{ color: '#4E5262' }}>FEATURE</span>
              </th>
              <th className="px-6 py-4 text-center font-normal" style={{ color: '#8A8D9A' }}>Bloomberg</th>
              <th className="px-6 py-4 text-center font-normal" style={{ color: '#8A8D9A' }}>Manual</th>
              <th className="px-6 py-4 text-center font-semibold" style={{ color: '#C9A84C' }}>EREBUS</th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row, i) => (
              <tr
                key={i}
                style={{
                  borderBottom: '1px solid rgba(255,255,255,0.05)',
                  background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)',
                }}
              >
                <td className="px-6 py-3.5 text-[13px]" style={{ color: '#EEE9E0' }}>{row.feature}</td>
                <td className="px-6 py-3.5 text-center">
                  {row.bloombergVal
                    ? <span className="font-jetbrains text-[12px]" style={{ color: '#8A8D9A' }}>{row.bloombergVal}</span>
                    : <Tick ok={row.bloomberg} />}
                </td>
                <td className="px-6 py-3.5 text-center">
                  {row.manualVal
                    ? <span className="font-jetbrains text-[12px]" style={{ color: '#8A8D9A' }}>{row.manualVal}</span>
                    : <Tick ok={row.manual} />}
                </td>
                <td className="px-6 py-3.5 text-center">
                  {row.erebusVal
                    ? <span className="font-jetbrains text-[12px] font-semibold" style={{ color: '#C9A84C' }}>{row.erebusVal}</span>
                    : <Tick ok={row.erebus} />}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
