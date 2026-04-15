// src/components/landing/FeatureGrid.jsx
import { useRef, useEffect } from 'react'
import { FileStack, ShieldCheck, Cpu, BookOpen, GitCompare, LineChart } from 'lucide-react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const FEATURES = [
  {
    icon: FileStack,
    accent: '#4A8FE7',
    title: 'Multi-format Ingestion',
    desc: 'PDFs, earnings transcripts, SEBI filings, structured CSVs — all chunked, embedded, and indexed with full source lineage.',
    tag: 'RAG Pipeline',
  },
  {
    icon: ShieldCheck,
    accent: '#2ECC8A',
    title: 'Zero-Hallucination Reasoning',
    desc: 'Every claim cites a document, page number, and timestamp. The system refuses to guess — it only speaks from evidence.',
    tag: 'Source-Grounded',
  },
  {
    icon: Cpu,
    accent: '#C9A84C',
    title: '8-Alpha Signal Engine',
    desc: 'Growth, Margin, Consistency, Risk, Volatility, Credibility, Sentiment, Relative Strength — computed deterministically.',
    tag: 'Quant Layer',
  },
  {
    icon: BookOpen,
    accent: '#E09A25',
    title: 'Company Scorecards',
    desc: 'Dimension-wise scoring with evidence-backed reasoning across industry position, financial quality, and management credibility.',
    tag: 'Output Layer',
  },
  {
    icon: LineChart,
    accent: '#D95555',
    title: 'Guidance Tracker',
    desc: '4-quarter tracking of what management promised vs what was delivered — with deviation patterns highlighted and scored.',
    tag: 'NLP Parser',
  },
  {
    icon: GitCompare,
    accent: '#8B6FF0',
    title: 'Cross-Company Ranking',
    desc: 'Peer analysis across 3+ metrics with percentile positioning, relative scores, and insight differentiation per dimension.',
    tag: 'Compare Engine',
  },
]

export default function FeatureGrid() {
  const sectionRef = useRef(null)
  const cardRefs   = useRef([])

  useEffect(() => {
    const ctx = gsap.context(() => {
      cardRefs.current.forEach((el, i) => {
        if (!el) return
        gsap.fromTo(
          el,
          { opacity: 0, y: 32 },
          {
            opacity: 1,
            y: 0,
            duration: 0.7,
            ease: 'power3.out',
            scrollTrigger: {
              trigger: el,
              start: 'top 88%',
            },
            delay: (i % 3) * 0.1,
          }
        )
      })
    }, sectionRef)
    return () => ctx.revert()
  }, [])

  return (
    <section
      ref={sectionRef}
      id="research"
      className="py-28 px-8 lg:px-20 bg-erebus-bg"
    >
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <div className="section-label mb-5">Capabilities</div>
          <h2 className="font-serif text-[42px] md:text-[50px] text-erebus-text-1 leading-[1.1] mb-4">
            One agent. Six intelligence layers.
          </h2>
          <p className="text-[16px] text-erebus-text-2 max-w-lg mx-auto leading-relaxed">
            Each layer feeds the next. Every output is traceable to its source.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map((f, i) => {
            const Icon = f.icon
            return (
              <div
                key={i}
                ref={el => { cardRefs.current[i] = el }}
                className="elevated rounded-xl p-7 card-interactive cursor-default group"
                style={{ opacity: 0 }}
              >
                {/* Icon container */}
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center mb-5"
                  style={{
                    background: `${f.accent}12`,
                    border: `1px solid ${f.accent}20`,
                  }}
                >
                  <Icon size={18} style={{ color: f.accent }} />
                </div>

                {/* Tag */}
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-[15px] font-semibold text-erebus-text-1">
                    {f.title}
                  </h3>
                  <span
                    className="text-[10px] font-mono px-2 py-0.5 rounded"
                    style={{
                      background: `${f.accent}10`,
                      color: f.accent,
                      border: `1px solid ${f.accent}18`,
                    }}
                  >
                    {f.tag}
                  </span>
                </div>

                <p className="text-[13px] text-erebus-text-2 leading-[1.75]">
                  {f.desc}
                </p>

                {/* Hover accent line */}
                <div
                  className="h-px mt-6 w-0 group-hover:w-full transition-all duration-500"
                  style={{ background: `linear-gradient(to right, ${f.accent}40, transparent)` }}
                />
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
