// src/components/landing/ArchDiagram.jsx
// Architecture diagram — animated layer stack with GSAP ScrollTrigger
import { useRef, useEffect } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const LAYERS = [
  {
    label:   'INGESTION LAYER',
    models:  ['PDF / TXT / CSV Parser', 'SEBI Filing Sync', 'Source Lineage Tracker'],
    accent:  '#4A8FE7',
    index:   '01',
  },
  {
    label:   'RETRIEVAL LAYER',
    models:  ['BGE-M3 Embeddings', 'FAISS Vector Store', 'BM25 Hybrid Search'],
    accent:  '#C9A84C',
    index:   '02',
  },
  {
    label:   'LANGUAGE LAYER',
    models:  ['Gemini 1.5 Pro (Primary)', 'Claude Sonnet (Validation)', '128K Context Window'],
    accent:  '#8B6FF0',
    index:   '03',
  },
  {
    label:   'QUANTITATIVE CORE',
    models:  ['8 Alpha Signal Engine', 'DCF + Valuation', 'Peer Ratio Matrix'],
    accent:  '#2ECC8A',
    index:   '04',
  },
  {
    label:   'NLP / SIGNAL LAYER',
    models:  ['Guidance NLP Parser', 'Sentiment Classifier', 'Credibility Scorer'],
    accent:  '#E09A25',
    index:   '05',
  },
  {
    label:   'OUTPUT LAYER',
    models:  ['Structured JSON → UI', 'Citation Linker', 'Evidence Tracer'],
    accent:  '#C9A84C',
    index:   '06',
  },
]

export default function ArchDiagram() {
  const sectionRef = useRef(null)
  const layerRefs  = useRef([])

  useEffect(() => {
    const ctx = gsap.context(() => {
      layerRefs.current.forEach((el, i) => {
        if (!el) return
        gsap.fromTo(
          el,
          { opacity: 0, x: -24 },
          {
            opacity: 1,
            x: 0,
            duration: 0.6,
            ease: 'power3.out',
            delay: i * 0.08,
            scrollTrigger: {
              trigger: sectionRef.current,
              start: 'top 70%',
            },
          }
        )
      })
    }, sectionRef)
    return () => ctx.revert()
  }, [])

  return (
    <section
      ref={sectionRef}
      id="architecture"
      className="py-28 px-8 lg:px-20 bg-erebus-bg"
    >
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <div className="section-label mb-5">Architecture</div>
          <h2 className="font-serif text-[42px] md:text-[50px] text-erebus-text-1 leading-[1.1] mb-4">
            Built in layers. Reasoned end-to-end.
          </h2>
          <p className="text-[15px] text-erebus-text-2 max-w-lg mx-auto">
            Every query passes through all six layers before a single word is generated. No shortcuts.
          </p>
        </div>

        <div className="relative">
          {/* Vertical connector line */}
          <div
            className="absolute left-[28px] top-5 bottom-5 w-px"
            style={{ background: 'linear-gradient(to bottom, transparent, rgba(255,255,255,0.06) 20%, rgba(255,255,255,0.06) 80%, transparent)' }}
          />

          <div className="flex flex-col gap-3">
            {LAYERS.map((layer, i) => (
              <div
                key={i}
                ref={el => { layerRefs.current[i] = el }}
                className="relative flex items-center gap-5"
                style={{ opacity: 0 }}
              >
                {/* Index node */}
                <div
                  className="w-14 h-14 rounded-lg shrink-0 flex items-center justify-center z-10"
                  style={{
                    background: `${layer.accent}0E`,
                    border: `1px solid ${layer.accent}25`,
                  }}
                >
                  <span
                    className="font-mono text-[11px] font-medium"
                    style={{ color: layer.accent }}
                  >
                    {layer.index}
                  </span>
                </div>

                {/* Layer card */}
                <div
                  className="flex-1 flex flex-col sm:flex-row sm:items-center gap-3 px-5 py-4 rounded-lg"
                  style={{
                    background: '#0F1117',
                    border: '1px solid rgba(255,255,255,0.06)',
                    borderLeft: `3px solid ${layer.accent}`,
                  }}
                >
                  <span
                    className="font-mono text-[11px] tracking-[0.1em] shrink-0 w-40"
                    style={{ color: layer.accent }}
                  >
                    {layer.label}
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {layer.models.map(m => (
                      <span
                        key={m}
                        className="text-[11px] text-erebus-text-2 px-2.5 py-1 rounded"
                        style={{
                          background: 'rgba(255,255,255,0.04)',
                          border: '1px solid rgba(255,255,255,0.07)',
                        }}
                      >
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
