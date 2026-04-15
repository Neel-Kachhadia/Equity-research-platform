# EREBUS — React + Tailwind Frontend Specification
> All component file extensions changed from `.tsx` → `.jsx`. All TypeScript types, interfaces, and type annotations removed. Props, state, and function signatures are plain JavaScript.

---

## 1. PRODUCT VISION & POSITIONING

**Product Name:** EREBUS
**Tagline:** *Institutional-grade equity intelligence. For everyone.*
**Positioning:** EREBUS is the Bloomberg Terminal of the AI era — but designed for the analyst who doesn't have $24,000/year to spend. It replaces scattered manual research with a single, deeply intelligent agent that reads filings, reasons across time, and speaks in evidence.

**Target Users:**
- Retail analysts & SEBI-registered investment advisors
- Mid-size asset management firms without quant teams
- Fintech startups building research automation
- Equity research interns at brokerages

---

## 2. BRAND & DESIGN SYSTEM

### Tailwind Config Extension (`tailwind.config.js`)

```js
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        'erebus-bg':        '#0D0F14',
        'erebus-surface':   '#13161E',
        'erebus-surface-2': '#1A1E2A',
        'erebus-gold':      '#C9A84C',
        'erebus-blue':      '#4A8FE7',
        'erebus-green':     '#3ECF8E',
        'erebus-red':       '#E55C5C',
        'erebus-amber':     '#F0A429',
        'erebus-text-1':    '#F0EDE6',
        'erebus-text-2':    '#8B8E99',
        'erebus-text-3':    '#545769',
      },
      fontFamily: {
        sans:  ['Inter', 'sans-serif'],
        serif: ['"DM Serif Display"', 'serif'],
        mono:  ['"JetBrains Mono"', 'monospace'],
      },
      fontSize: {
        '11': '11px', '13': '13px', '22': '22px',
        '28': '28px', '36': '36px', '48': '48px',
        '64': '64px', '72': '72px', '80': '80px',
      },
      borderRadius: {
        'sm':  '6px',
        'md':  '8px',
        'lg':  '12px',
        'xl':  '16px',
      },
      spacing: {
        '4':   '4px',   '12': '12px',  '16': '16px',
        '20':  '20px',  '24': '24px',  '32': '32px',
        '48':  '48px',  '64': '64px',  '80': '80px',
        '96':  '96px',  '128':'128px',
      },
      keyframes: {
        'fade-up': {
          '0%':   { opacity: '0', transform: 'translateY(40px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-dot': {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.3' },
        },
        'bounce-chevron': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%':      { transform: 'translateY(-6px)' },
        },
        'dash-draw': {
          from: { strokeDashoffset: '200' },
          to:   { strokeDashoffset: '0' },
        },
        'ripple': {
          from: { transform: 'scale(0)', opacity: '1' },
          to:   { transform: 'scale(1.5)', opacity: '0' },
        },
      },
      animation: {
        'fade-up':        'fade-up 0.6s ease forwards',
        'pulse-dot':      'pulse-dot 1.2s infinite',
        'bounce-chevron': 'bounce-chevron 2s ease-in-out infinite',
        'dash-draw':      'dash-draw 1s ease forwards',
        'ripple':         'ripple 1.5s ease-out infinite',
      },
    },
  },
  plugins: [],
}
```

### CSS Variables (in `src/index.css`)

```css
/* src/index.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=DM+Serif+Display:ital@0;1&family=JetBrains+Mono:wght@400;500&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --erebus-border:       rgba(255,255,255,0.07);
  --erebus-border-hover: rgba(255,255,255,0.14);
  --erebus-gold-dim:     rgba(201,168,76,0.12);
  --erebus-gold-glow:    rgba(201,168,76,0.08);
  --erebus-blue-dim:     rgba(74,143,231,0.12);
}

/* Custom scrollbar */
::-webkit-scrollbar       { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.05); border-radius: 2px; }

/* Staggered word animations */
.word-anim { animation: fade-up 0.6s ease forwards; opacity: 0; }

@layer components {
  /* Input focus ring */
  .input-erebus:focus {
    border-color: #C9A84C;
    box-shadow: 0 0 0 3px rgba(201,168,76,0.12);
  }

  /* Score bar fill */
  .bar-fill { transition: width 1s ease; }

  /* Context panel slide */
  .context-panel-enter { transform: translateX(320px); }
  .context-panel-enter-active {
    transform: translateX(0);
    transition: transform 280ms ease-out;
  }
}
```

---

## 3. PAGE ARCHITECTURE

```
erebus.ai/
├── /                       (Landing Page)
├── /login
├── /signup
└── /app
    ├── /app/chat           (default)
    ├── /app/research/:company
    ├── /app/scorecard
    ├── /app/compare
    └── /app/history
```

### Router Setup (`src/main.jsx`)

```jsx
// src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)
```

### App Root (`src/App.jsx`)

```jsx
// src/App.jsx
import { Routes, Route, Navigate } from 'react-router-dom'
import LandingPage   from './pages/LandingPage'
import LoginPage     from './pages/LoginPage'
import SignupPage    from './pages/SignupPage'
import AppShell      from './components/layout/AppShell'
import ChatPage      from './pages/app/ChatPage'
import ScorecardPage from './pages/app/ScorecardPage'
import ComparePage   from './pages/app/ComparePage'
import HistoryPage   from './pages/app/HistoryPage'

export default function App() {
  return (
    <Routes>
      <Route path="/"       element={<LandingPage />} />
      <Route path="/login"  element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/app"    element={<AppShell />}>
        <Route index        element={<Navigate to="chat" replace />} />
        <Route path="chat"       element={<ChatPage />} />
        <Route path="scorecard"  element={<ScorecardPage />} />
        <Route path="compare"    element={<ComparePage />} />
        <Route path="history"    element={<HistoryPage />} />
      </Route>
    </Routes>
  )
}
```

---

## 4. LANDING PAGE — `/`

### 4.1 Layout Structure
Full-page vertical scroll. Dark background `#0D0F14`. Sections:
1. Navbar
2. Hero
3. Problem Statement
4. Feature Grid
5. Architecture Diagram (animated)
6. Testimonials / Social Proof
7. Pricing
8. CTA Footer
9. Footer

### 4.2 NAVBAR (`src/components/landing/Navbar.jsx`)

```jsx
// src/components/landing/Navbar.jsx
import { Link } from 'react-router-dom'

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-50 h-16 flex items-center justify-between px-10
                    backdrop-blur-md bg-[rgba(13,15,20,0.85)]
                    border-b border-white/[0.06]">
      {/* Logo */}
      <div className="flex items-center gap-2">
        <div className="w-6 h-6 rounded-full bg-[var(--erebus-gold-dim)]
                        border border-erebus-gold flex items-center justify-center
                        font-serif text-erebus-gold text-sm">
          E
        </div>
        <span className="font-serif text-[18px] text-erebus-text-1 tracking-wide">
          EREBUS
        </span>
      </div>

      {/* Center links */}
      <div className="flex gap-8">
        {['Research', 'Architecture', 'Pricing', 'Docs'].map(link => (
          <a
            key={link}
            href={`#${link.toLowerCase()}`}
            className="text-sm text-erebus-text-2 hover:text-erebus-text-1
                       transition-colors duration-200"
          >
            {link}
          </a>
        ))}
      </div>

      {/* Right CTAs */}
      <div className="flex items-center gap-2.5">
        <Link
          to="/login"
          className="px-[18px] py-2 text-sm text-erebus-text-1 rounded-md
                     border border-white/[0.15] hover:border-erebus-gold
                     hover:text-erebus-gold transition-all duration-200"
        >
          Log in
        </Link>
        <Link
          to="/signup"
          className="px-[18px] py-2 text-sm font-semibold text-erebus-bg
                     bg-erebus-gold rounded-md hover:bg-[#D4B55C]
                     active:scale-[0.98] transition-all duration-150"
        >
          Start for free
        </Link>
      </div>
    </nav>
  )
}
```

**Specs:**
- Height: 64px
- Position: sticky top, `backdrop-filter: blur(12px)`, `background: rgba(13,15,20,0.85)`
- Border-bottom: `1px solid rgba(255,255,255,0.06)`
- Left: EREBUS logo — lettermark `E` in gold circle (24px) + wordmark in DM Serif Display 18px
- Center: Nav links — 14px Inter 400, `#8B8E99`, hover → `#F0EDE6` over 200ms
- Right: `Log in` (ghost) + `Start for free` (gold filled, `padding: 8px 18px`)
- Mobile: hamburger opens slide-down menu

---

### 4.3 HERO SECTION (`src/components/landing/Hero.jsx`)

```jsx
// src/components/landing/Hero.jsx
import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'

// Particle canvas — 60 gold dots, connection lines within 100px
function ParticleCanvas() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx    = canvas.getContext('2d')
    canvas.width  = canvas.offsetWidth
    canvas.height = canvas.offsetHeight

    const particles = Array.from({ length: 60 }, () => ({
      x:  Math.random() * canvas.width,
      y:  Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
    }))

    let raf
    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      particles.forEach(p => {
        p.x += p.vx; p.y += p.vy
        if (p.x < 0 || p.x > canvas.width)  p.vx *= -1
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1

        ctx.beginPath()
        ctx.arc(p.x, p.y, 1.5, 0, Math.PI * 2)
        ctx.fillStyle = 'rgba(201,168,76,0.4)'
        ctx.fill()
      })
      // connection lines
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx   = particles[i].x - particles[j].x
          const dy   = particles[i].y - particles[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 100) {
            ctx.beginPath()
            ctx.moveTo(particles[i].x, particles[i].y)
            ctx.lineTo(particles[j].x, particles[j].y)
            ctx.strokeStyle = `rgba(201,168,76,${0.15 * (1 - dist / 100)})`
            ctx.lineWidth = 0.5
            ctx.stroke()
          }
        }
      }
      raf = requestAnimationFrame(draw)
    }
    draw()
    return () => cancelAnimationFrame(raf)
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none"
    />
  )
}

export default function Hero() {
  return (
    <section className="relative h-screen flex flex-col items-center
                        justify-center text-center px-6 bg-erebus-bg overflow-hidden">
      <ParticleCanvas />

      {/* Section pill */}
      <div className="word-anim [animation-delay:0ms] relative z-10
                      px-[14px] py-1 rounded-full text-[11px] font-medium
                      tracking-[0.12em] text-erebus-gold
                      bg-[var(--erebus-gold-dim)]
                      border border-erebus-gold/30 mb-7">
        SECTION ALPHA · EQUITY RESEARCH AI
      </div>

      {/* H1 — words stagger via inline animation-delay */}
      <h1 className="relative z-10 leading-[1.1] mb-6">
        {/* Line 1 */}
        <span className="block font-serif text-[72px] text-erebus-text-1">
          {['The', 'research', 'layer'].map((w, i) => (
            <span
              key={w}
              className="inline-block mr-4 word-anim"
              style={{ animationDelay: `${i * 80}ms` }}
            >
              {w}
            </span>
          ))}
        </span>
        {/* Line 2 */}
        <span className="block font-serif italic text-[72px] text-erebus-gold">
          {['Indian', 'equity', 'deserves.'].map((w, i) => (
            <span
              key={w}
              className="inline-block mr-4 word-anim"
              style={{ animationDelay: `${(i + 3) * 80}ms` }}
            >
              {w}
            </span>
          ))}
        </span>
      </h1>

      {/* Subheadline */}
      <p className="word-anim [animation-delay:600ms] relative z-10
                    text-[18px] text-erebus-text-2 max-w-[600px]
                    leading-[1.7] mb-10">
        EREBUS ingests filings, transcripts, and structured data — then reasons
        across companies, time, and risk to produce analyst-grade intelligence
        with zero hallucination.
      </p>

      {/* CTA row */}
      <div className="word-anim [animation-delay:700ms] relative z-10
                      flex gap-4 justify-center mb-10">
        <Link
          to="/app"
          className="px-7 py-[14px] text-[16px] font-semibold text-erebus-bg
                     bg-erebus-gold rounded-md hover:bg-[#D4B55C]
                     active:scale-[0.98] transition-all duration-150"
        >
          Start analysing →
        </Link>
        <button
          className="px-7 py-[14px] text-[16px] text-erebus-text-1 rounded-md
                     border border-white/[0.15] hover:border-erebus-gold
                     hover:text-erebus-gold transition-all duration-200"
        >
          ▶ Watch 3-min demo
        </button>
      </div>

      {/* Company logos row */}
      <p className="word-anim [animation-delay:800ms] relative z-10
                    text-[13px] text-erebus-text-3">
        Covering India's top sectors — NSE / BSE listed companies
      </p>

      {/* Scroll chevron */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2
                      text-erebus-gold text-xl animate-bounce-chevron">
        ⌄
      </div>
    </section>
  )
}
```

**Specs:**
- Height: 100vh
- Background: `#0D0F14` — NO gradients. Canvas particle field (60 particles, gold rgba, connection lines ≤100px)
- Pill badge above headline: gold, 11px Inter 500, letter-spacing 0.12em
- H1: DM Serif Display 72px / italic 72px gold. Words stagger 80ms each via GSAP or CSS `animation-delay`
- Subheadline: Inter 18px, `#8B8E99`, max-width 600px
- CTA: gold filled `Start analysing →` + ghost `Watch demo`
- Scroll chevron: bouncing, `#C9A84C`, fades after first scroll

---

### 4.4 PROBLEM STATEMENT (`src/components/landing/ProblemStatement.jsx`)

```jsx
// src/components/landing/ProblemStatement.jsx
export default function ProblemStatement() {
  const bullets = [
    'Exchange filings, transcripts, IR pages — siloed and unstructured',
    'Generic AI hallucinates financial data and lacks source tracing',
    'Institutional tools cost ₹20L+/year — out of reach for most',
  ]

  return (
    <section className="py-24 px-20 flex gap-16 items-center bg-erebus-bg">
      {/* Left 60% */}
      <div className="flex-[0_0_60%]">
        <p className="font-serif text-[48px] text-erebus-text-1 leading-[1.15]">
          The information exists.
        </p>
        <p className="font-serif italic text-[48px] text-erebus-gold
                      leading-[1.15] mb-8">
          The problem is it's scattered everywhere.
        </p>
        <ul className="space-y-4">
          {bullets.map((b, i) => (
            <li key={i} className="flex gap-3 items-start">
              <span className="text-erebus-amber mt-1">·</span>
              <span className="text-[16px] text-erebus-text-2 leading-[1.8]">{b}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Right 40% — data scatter visual */}
      {/* Use GSAP ScrollTrigger: docs float randomly → collapse into gold E core */}
      <div className="flex-1 relative h-64 bg-erebus-surface rounded-xl
                      border border-[var(--erebus-border)] overflow-hidden p-6">
        {/* Floating document chips — animate with GSAP on scroll */}
        {['Annual Report PDF', 'Earnings Transcript', 'Balance Sheet CSV', 'SEBI Filing'].map((d, i) => (
          <div
            key={d}
            className="absolute flex items-center gap-2 px-3 py-2
                       bg-erebus-surface-2 rounded-lg text-[13px]
                       text-erebus-text-2 border border-[var(--erebus-border)]
                       opacity-70"
            style={{ top: `${15 + i * 18}%`, left: `${5 + i * 15}%` }}
            // data-gsap="scatter" — target with ScrollTrigger in parent
          >
            <span>📄</span> {d}
          </div>
        ))}
        {/* EREBUS core node — target with GSAP collapse animation */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-0"
             data-gsap="core">
          <div className="w-12 h-12 rounded-full border-2 border-erebus-gold
                          bg-[var(--erebus-gold-dim)] flex items-center
                          justify-content font-serif text-erebus-gold text-xl">
            E
          </div>
        </div>
      </div>
    </section>
  )
}
```

**Specs:**
- Padding: 96px 0
- Left column (60%): DM Serif Display 48px headline + italic gold + amber-bulleted list
- Right column (40%): GSAP ScrollTrigger — docs float randomly → collapse into gold `E` core node
- Each bullet: 16px Inter, `#8B8E99`, line-height 1.8

---

### 4.5 FEATURE GRID (`src/components/landing/FeatureGrid.jsx`)

```jsx
// src/components/landing/FeatureGrid.jsx
const features = [
  {
    icon: '📄',
    title: 'Multi-format Ingestion',
    desc:  'PDFs, earnings transcripts, SEBI filings, structured CSVs — all chunked, embedded, and indexed with source lineage.',
  },
  {
    icon: '🔍',
    title: 'Zero-hallucination RAG',
    desc:  'Every claim cites a document, page number, and timestamp. The system refuses to guess.',
  },
  {
    icon: '📊',
    title: '8-Alpha Signal Engine',
    desc:  'Growth, Margin, Consistency, Risk, Volatility, Credibility, Sentiment, Relative Strength — each computed deterministically.',
  },
  {
    icon: '🎯',
    title: 'Company Scorecards',
    desc:  'Dimension-wise scoring with evidence-backed reasoning across industry position, financial quality, management credibility, and risk.',
  },
  {
    icon: '🔄',
    title: 'Mgmt Guidance Tracker',
    desc:  '4-quarter tracking of what was promised vs what was delivered — with deviation patterns highlighted.',
  },
  {
    icon: '⚖️',
    title: 'Cross-company Ranking',
    desc:  'Peer analysis across 3+ metrics with positioning, percentile rank, and insight differentiation.',
  },
]

export default function FeatureGrid() {
  return (
    <section id="research" className="py-16 px-20 bg-erebus-bg">
      <h2 className="font-serif text-[40px] text-center text-erebus-text-1 mb-2">
        One agent. Five capabilities.
      </h2>
      <p className="text-[16px] text-erebus-text-2 text-center mb-16">
        Each layer feeds the next.
      </p>

      <div className="grid grid-cols-3 gap-6">
        {features.map((f, i) => (
          <div
            key={i}
            className="p-7 bg-erebus-surface rounded-lg
                       border border-[var(--erebus-border)]
                       hover:border-erebus-gold/25 hover:bg-erebus-surface-2
                       transition-all duration-[250ms] cursor-default"
          >
            <div className="w-8 h-8 mb-4 rounded-md bg-[var(--erebus-gold-dim)]
                            flex items-center justify-center text-[16px]">
              {f.icon}
            </div>
            <h3 className="text-[15px] font-semibold text-erebus-text-1 mb-2">
              {f.title}
            </h3>
            <p className="text-[13px] text-erebus-text-2 leading-[1.7]">
              {f.desc}
            </p>
          </div>
        ))}
      </div>
    </section>
  )
}
```

**Card specs:**
- `background: #13161E` → `bg-erebus-surface`
- `border: 1px solid rgba(255,255,255,0.07)` → `border-[var(--erebus-border)]`
- `border-radius: 12px` → `rounded-lg`
- `padding: 28px` → `p-7`
- Icon container: 32×32px, `background: rgba(201,168,76,0.1)`, `border-radius: 8px`
- Hover: border → `rgba(201,168,76,0.25)`, bg → `#1A1E2A`, transition 250ms

---

### 4.6 ARCHITECTURE DIAGRAM (`src/components/landing/ArchDiagram.jsx`)

```jsx
// src/components/landing/ArchDiagram.jsx
// Use GSAP ScrollTrigger to animate stroke-dashoffset of SVG connector lines
// and fade-up each layer box as it enters viewport.

const layers = [
  {
    label:  'RETRIEVAL LAYER',
    models: ['BGE-M3 Embeddings', 'FAISS Vector Store', 'BM25 Hybrid'],
    accent: '#C9A84C',
  },
  {
    label:  'LANGUAGE LAYER',
    models: ['Gemini 1.5 Pro (Primary)', 'Claude Sonnet (Validation)', '128K Context'],
    accent: '#4A8FE7',
  },
  {
    label:  'QUANTITATIVE CORE',
    models: ['8 Alpha Signals', 'DCF Engine', 'Peer Ratios'],
    accent: '#3ECF8E',
  },
  {
    label:  'NLP / SIGNAL',
    models: ['Guidance NLP Parser', 'Sentiment Classifier', 'Credibility Scorer'],
    accent: '#F0A429',
  },
  {
    label:  'OUTPUT LAYER',
    models: ['JSON → Structured UI', 'Citation Linker', 'Evidence Tracer'],
    accent: '#C9A84C',
  },
]

export default function ArchDiagram() {
  return (
    <section id="architecture" className="py-20 px-20 bg-erebus-bg">
      <h2 className="font-serif text-[40px] text-center text-erebus-text-1 mb-4">
        Built in layers. Reasoned end-to-end.
      </h2>
      <p className="text-[15px] text-erebus-text-2 text-center mb-14">
        Every query passes through all five layers before a single word is generated.
      </p>

      <div className="relative max-w-2xl mx-auto flex flex-col gap-0">
        {layers.map((layer, i) => (
          <div key={i}>
            {/* Layer box */}
            <div
              className="bg-erebus-surface rounded-[0_12px_12px_0]
                         border border-erebus-gold/20 p-5"
              style={{ borderLeft: `4px solid ${layer.accent}` }}
              // data-gsap="arch-layer" for ScrollTrigger fade-in
            >
              <div className="flex items-center justify-between">
                <span
                  className="font-mono text-[11px] tracking-[0.1em]"
                  style={{ color: layer.accent }}
                >
                  {layer.label}
                </span>
                <div className="flex gap-2">
                  {layer.models.map(m => (
                    <span
                      key={m}
                      className="text-[11px] text-erebus-text-2 px-2 py-0.5
                                 rounded bg-white/[0.04]
                                 border border-white/[0.08]"
                    >
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Animated SVG connector (hidden on last item) */}
            {i < layers.length - 1 && (
              <div className="flex justify-center my-0.5">
                <svg width="20" height="16" viewBox="0 0 20 16" fill="none">
                  <path
                    d="M10 0 L10 10 M6 6 L10 10 L14 6"
                    stroke="rgba(201,168,76,0.4)"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeDasharray="200"
                    strokeDashoffset="200"
                    className="animate-dash-draw"
                    // data-gsap="arch-arrow" for ScrollTrigger stroke-dashoffset
                  />
                </svg>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
```

**Specs:**
- Background: `#0D0F14`
- Trigger: ScrollTrigger — elements draw in as section enters viewport
- Layer box: `background: #13161E`, `border: 1px solid rgba(201,168,76,0.2)`, gold left-border `4px solid #C9A84C`
- Arrows: animated `stroke-dashoffset` SVG lines in gold
- Layer labels: JetBrains Mono, 12px, `#C9A84C`
- Model labels: Inter 13px, `#F0EDE6`

---

### 4.7 TESTIMONIALS (`src/components/landing/Testimonials.jsx`)

```jsx
// src/components/landing/Testimonials.jsx
const testimonials = [
  {
    quote:   'Finally replaced my Bloomberg dependency for Indian mid-cap research. The guidance tracker alone saves me 4 hours a week.',
    initials:'AR',
    name:    'Arjun Rao',
    role:    'Senior Analyst',
    firm:    'Motilal Oswal',
  },
  {
    quote:   'The zero-hallucination claim is actually true. Every number cites its source — I can verify in seconds.',
    initials:'PM',
    name:    'Priya Menon',
    role:    'Portfolio Manager',
    firm:    'Mirae Asset',
  },
  {
    quote:   'We built our internal research workflow on top of EREBUS API. Interns produce institutional-grade notes from day one.',
    initials:'SK',
    name:    'Sameer Kapoor',
    role:    'Head of Research',
    firm:    'Edelweiss',
  },
]

export default function Testimonials() {
  return (
    <section className="py-20 px-20 bg-erebus-bg">
      <div className="grid grid-cols-3 gap-5">
        {testimonials.map((t, i) => (
          <div
            key={i}
            className="bg-erebus-surface rounded-lg border border-[var(--erebus-border)] p-7"
          >
            <p className="font-serif italic text-[15px] text-erebus-text-1 leading-[1.7] mb-6">
              "{t.quote}"
            </p>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[var(--erebus-gold-dim)]
                              flex items-center justify-center
                              text-erebus-gold text-[13px] font-semibold">
                {t.initials}
              </div>
              <div>
                <p className="text-[14px] font-medium text-erebus-text-1">{t.name}</p>
                <p className="text-[13px] text-erebus-text-2">{t.role}</p>
              </div>
              <span className="ml-auto text-[11px] text-erebus-blue px-2 py-0.5 rounded-full
                               bg-[var(--erebus-blue-dim)]">
                {t.firm}
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
```

---

### 4.8 PRICING (`src/components/landing/Pricing.jsx`)

```jsx
// src/components/landing/Pricing.jsx
import { Link } from 'react-router-dom'

const plans = [
  {
    name:     'Free',
    price:    '₹0',
    period:   '/mo',
    features: [
      { text: '5 queries / day',          active: true  },
      { text: 'Basic scorecard',          active: true  },
      { text: '2 company watchlist',      active: true  },
      { text: 'Community support',        active: true  },
      { text: 'SEBI filing ingestion',    active: false },
      { text: 'Guidance tracker',         active: false },
    ],
    cta:     'Get started',
    to:      '/signup',
    popular: false,
  },
  {
    name:     'Pro',
    price:    '₹2,999',
    period:   '/mo',
    features: [
      { text: 'Unlimited queries',        active: true },
      { text: 'Full 8-alpha engine',      active: true },
      { text: 'Unlimited companies',      active: true },
      { text: 'Priority support',         active: true },
      { text: 'SEBI filing ingestion',    active: true },
      { text: 'Guidance tracker',         active: true },
    ],
    cta:     'Start Pro trial',
    to:      '/signup',
    popular: true,
  },
  {
    name:     'Enterprise',
    price:    'Custom',
    period:   '',
    features: [
      { text: 'Everything in Pro',        active: true },
      { text: 'API access',               active: true },
      { text: 'Custom data ingestion',    active: true },
      { text: 'Dedicated compute',        active: true },
      { text: 'SLA guarantee',            active: true },
    ],
    cta:     'Contact us',
    to:      '/contact',
    popular: false,
  },
]

export default function Pricing() {
  return (
    <section id="pricing" className="py-20 px-20 bg-erebus-bg">
      <h2 className="font-serif text-[40px] text-center text-erebus-text-1 mb-14">
        Simple pricing. Serious research.
      </h2>

      <div className="grid grid-cols-3 gap-5 max-w-4xl mx-auto">
        {plans.map(plan => (
          <div
            key={plan.name}
            className={`relative bg-erebus-surface rounded-xl p-8
              ${plan.popular
                ? 'border border-erebus-gold/50'
                : 'border border-[var(--erebus-border)]'
              }`}
          >
            {plan.popular && (
              <div className="absolute -top-3.5 left-1/2 -translate-x-1/2
                              px-3 py-0.5 rounded-full text-[11px] font-medium
                              text-erebus-gold bg-[var(--erebus-gold-dim)]
                              border border-erebus-gold/30 whitespace-nowrap">
                ★ Most popular
              </div>
            )}

            <p className="text-[13px] text-erebus-text-2 mb-2">{plan.name}</p>
            <div className="flex items-baseline gap-1 mb-6">
              <span className={`font-serif text-[44px]
                ${plan.popular ? 'text-erebus-gold' : 'text-erebus-text-1'}`}>
                {plan.price}
              </span>
              {plan.period && (
                <span className="text-[14px] text-erebus-text-2">{plan.period}</span>
              )}
            </div>

            <ul className="space-y-2.5 mb-6">
              {plan.features.map(f => (
                <li key={f.text} className="flex items-center gap-2 text-[13px]">
                  <span className={f.active ? 'text-erebus-green' : 'text-erebus-text-3'}>
                    {f.active ? '✓' : '–'}
                  </span>
                  <span className={f.active ? 'text-erebus-text-2' : 'text-erebus-text-3 line-through'}>
                    {f.text}
                  </span>
                </li>
              ))}
            </ul>

            <Link
              to={plan.to}
              className={`block w-full text-center py-3 rounded-md text-[14px] font-medium
                transition-all duration-150 active:scale-[0.98]
                ${plan.popular
                  ? 'bg-erebus-gold text-erebus-bg hover:bg-[#D4B55C]'
                  : 'border border-white/[0.15] text-erebus-text-1 hover:border-erebus-gold hover:text-erebus-gold'
                }`}
            >
              {plan.cta}
            </Link>
          </div>
        ))}
      </div>
    </section>
  )
}
```

---

### 4.9 FOOTER (`src/components/landing/Footer.jsx`)

```jsx
// src/components/landing/Footer.jsx
const cols = {
  Product: ['Chat', 'Scorecard', 'Compare', 'History'],
  Company: ['About', 'Careers', 'Blog', 'Press'],
  Legal:   ['Privacy Policy', 'Terms of Service', 'Cookie Policy'],
}

export default function Footer() {
  return (
    <footer className="px-20 pt-12 pb-6 border-t border-white/[0.06] bg-erebus-bg">
      <div className="flex justify-between mb-10">
        {/* Logo + tagline */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <div className="w-6 h-6 rounded-full border border-erebus-gold
                            bg-[var(--erebus-gold-dim)] flex items-center
                            justify-center font-serif text-erebus-gold text-sm">
              E
            </div>
            <span className="font-serif text-[18px] text-erebus-text-1">EREBUS</span>
          </div>
          <p className="text-[13px] text-erebus-text-3">
            Institutional-grade equity intelligence.
          </p>
        </div>
        {/* Link columns */}
        {Object.entries(cols).map(([sec, links]) => (
          <div key={sec}>
            <p className="text-[12px] text-erebus-text-3 uppercase tracking-[0.08em] mb-3">
              {sec}
            </p>
            {links.map(l => (
              <p key={l} className="text-[13px] text-erebus-text-2 mb-2 cursor-pointer
                                    hover:text-erebus-text-1 transition-colors duration-150">
                {l}
              </p>
            ))}
          </div>
        ))}
      </div>
      <div className="border-t border-white/[0.06] pt-5 text-[12px] text-erebus-text-3">
        © 2025 EREBUS Technologies Pvt. Ltd. · SEBI Registration: INH000000000 ·
        Responses are for research only — not investment advice.
      </div>
    </footer>
  )
}
```

---

## 5. LOGIN PAGE — `/login` (`src/pages/LoginPage.jsx`)

### 5.1 Layout
Two-column split: Left 55% = GSAP animation panel, Right 45% = form. Both full viewport height.

```jsx
// src/pages/LoginPage.jsx
import LoginAnimation from '../components/auth/LoginAnimation'
import { useState }   from 'react'
import { Link }       from 'react-router-dom'

export default function LoginPage() {
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [loading,  setLoading]  = useState(false)

  function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    // call auth API
  }

  return (
    <div className="flex h-screen bg-erebus-bg">
      {/* Left animation panel */}
      <LoginAnimation />

      {/* Right form panel */}
      <div className="flex-[0_0_45%] bg-erebus-surface
                      border-l border-[var(--erebus-border)]
                      flex items-center justify-center px-10">
        <div className="w-full max-w-sm">
          {/* Logo */}
          <div className="flex items-center gap-2 mb-10">
            <div className="w-6 h-6 rounded-full border border-erebus-gold
                            bg-[var(--erebus-gold-dim)] flex items-center
                            justify-center font-serif text-erebus-gold text-sm">
              E
            </div>
            <span className="font-serif text-[22px] text-erebus-text-1">EREBUS</span>
          </div>

          <h1 className="text-[28px] font-medium text-erebus-text-1 mb-1">
            Welcome back
          </h1>
          <p className="text-[14px] text-erebus-text-2 mb-8">
            Sign in to your research workspace
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email */}
            <div>
              <label className="block text-[13px] text-erebus-text-2 mb-1.5">
                Email address
              </label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="input-erebus w-full bg-erebus-bg text-erebus-text-1
                           border border-white/10 rounded-md px-4 py-3
                           text-[15px] outline-none placeholder:text-erebus-text-3
                           focus:border-erebus-gold focus:ring-2
                           focus:ring-erebus-gold/10 transition-all"
                placeholder="you@example.com"
                required
              />
            </div>

            {/* Password */}
            <div>
              <div className="flex justify-between mb-1.5">
                <label className="text-[13px] text-erebus-text-2">Password</label>
                <a href="#" className="text-[13px] text-erebus-gold hover:underline">
                  Forgot password?
                </a>
              </div>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="input-erebus w-full bg-erebus-bg text-erebus-text-1
                             border border-white/10 rounded-md px-4 py-3 pr-11
                             text-[15px] outline-none placeholder:text-erebus-text-3
                             focus:border-erebus-gold focus:ring-2
                             focus:ring-erebus-gold/10 transition-all"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPass(p => !p)}
                  className="absolute right-3 top-1/2 -translate-y-1/2
                             text-erebus-text-3 hover:text-erebus-text-2 text-lg"
                >
                  {showPass ? '🙈' : '👁'}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full h-12 bg-erebus-gold text-erebus-bg rounded-md
                         text-[15px] font-semibold hover:bg-[#D4B55C]
                         active:scale-[0.98] transition-all duration-150
                         disabled:opacity-70 flex items-center justify-center gap-2"
            >
              {loading
                ? <span className="w-4 h-4 border-2 border-erebus-bg/30
                                   border-t-erebus-bg rounded-full animate-spin" />
                : 'Sign in'
              }
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-6">
            <div className="flex-1 h-px bg-white/[0.07]" />
            <span className="text-[13px] text-erebus-text-3">or continue with</span>
            <div className="flex-1 h-px bg-white/[0.07]" />
          </div>

          {/* OAuth */}
          <div className="grid grid-cols-2 gap-3">
            {['Google', 'Microsoft'].map(provider => (
              <button
                key={provider}
                className="h-11 flex items-center justify-center gap-2
                           bg-erebus-surface-2 border border-white/10
                           rounded-md text-[14px] text-erebus-text-1
                           hover:border-white/20 transition-colors"
              >
                {provider}
              </button>
            ))}
          </div>

          <p className="text-center text-[14px] text-erebus-text-2 mt-6">
            Don't have an account?{' '}
            <Link to="/signup" className="text-erebus-gold hover:underline">
              Sign up →
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
```

---

### 5.2 LOGIN ANIMATION (`src/components/auth/LoginAnimation.jsx`)

```jsx
// src/components/auth/LoginAnimation.jsx
// GSAP timeline: 5-phase loop
// Phase 1 (0–2s):   3 doc cards fly in from corners → converge center
// Phase 2 (2–3.5s): Gold radar rings expand from center; E lettermark spins in
// Phase 3 (3.5–5.5s): 8 alpha badges (α₁–α₈) spread into circle; labels fade in
// Phase 4 (5.5–7s): Badges collapse → scorecard card rises with animated bars
// Phase 5 (7–8s):   Everything fades out → restart loop

import { useEffect, useRef } from 'react'

const ALPHA_LABELS = [
  'Growth','Margin','Risk','Credibility',
  'Volatility','Consistency','Sentiment','Rel.Strength',
]

export default function LoginAnimation() {
  const containerRef = useRef(null)

  useEffect(() => {
    // Import GSAP dynamically (install: npm install gsap)
    // import gsap from 'gsap'
    // Build timeline here — see GSAP spec above
  }, [])

  return (
    <div
      ref={containerRef}
      className="flex-[0_0_55%] relative bg-erebus-bg overflow-hidden
                 flex items-center justify-center"
    >
      {/* Phase 1 — Document cards */}
      <div className="doc-card absolute opacity-0 bg-erebus-surface
                      border border-white/10 rounded-lg px-4 py-3
                      flex items-center gap-2 text-[13px] text-erebus-text-2">
        <span>📄</span> Annual Report FY24.pdf
      </div>
      <div className="doc-card absolute opacity-0 bg-erebus-surface
                      border border-white/10 rounded-lg px-4 py-3
                      flex items-center gap-2 text-[13px] text-erebus-text-2">
        <span>📝</span> Q4 Earnings Transcript.txt
      </div>
      <div className="doc-card absolute opacity-0 bg-erebus-surface
                      border border-white/10 rounded-lg px-4 py-3
                      flex items-center gap-2 text-[13px] text-erebus-text-2">
        <span>📊</span> Balance Sheet FY24.csv
      </div>

      {/* Phase 2 — Radar rings + E mark */}
      <div className="radar-ring absolute w-20 h-20 rounded-full
                      border border-erebus-gold/40 scale-0 opacity-0" />
      <div className="radar-ring absolute w-20 h-20 rounded-full
                      border border-erebus-gold/30 scale-0 opacity-0" />
      <div className="e-mark absolute opacity-0 w-14 h-14 rounded-full
                      border-2 border-erebus-gold bg-[var(--erebus-gold-dim)]
                      flex items-center justify-center
                      font-serif text-erebus-gold text-2xl">
        E
      </div>

      {/* Phase 3 — Alpha badges */}
      {ALPHA_LABELS.map((label, i) => (
        <div
          key={label}
          className="alpha-badge absolute opacity-0 flex items-center gap-2"
        >
          <div className="w-9 h-9 rounded-full bg-[var(--erebus-gold-dim)]
                          border border-erebus-gold flex items-center
                          justify-center font-mono text-[12px] text-erebus-gold">
            α{i + 1}
          </div>
          <span className="text-[12px] text-erebus-text-2 whitespace-nowrap">
            {label}
          </span>
        </div>
      ))}

      {/* Phase 4 — Scorecard */}
      <div className="scorecard absolute opacity-0 w-72 bg-erebus-surface
                      border border-[var(--erebus-border)] rounded-lg p-5">
        <p className="font-mono text-[11px] text-erebus-text-3 mb-1">HDFC BANK · FY24</p>
        <p className="font-mono text-[40px] text-erebus-green mb-4">74</p>
        {ALPHA_LABELS.slice(0, 5).map((label, i) => (
          <div key={label} className="flex items-center gap-3 mb-2.5">
            <span className="text-[12px] text-erebus-text-2 w-24 shrink-0">{label}</span>
            <div className="flex-1 h-1 bg-white/[0.06] rounded-full overflow-hidden">
              <div
                className="h-full bg-erebus-green rounded-full bar-fill"
                style={{ width: `${60 + i * 5}%` }}
              />
            </div>
            <span className="font-mono text-[12px] text-erebus-text-1 w-7 text-right">
              {60 + i * 5}
            </span>
          </div>
        ))}
      </div>

      {/* Static footer label */}
      <p className="absolute bottom-5 left-1/2 -translate-x-1/2
                    font-mono text-[10px] text-erebus-text-3 tracking-[0.1em] whitespace-nowrap">
        EREBUS · RETRIEVAL & KNOWLEDGE · QUANTITATIVE CORE · NLP SIGNAL
      </p>
    </div>
  )
}
```

---

## 6. SIGNUP PAGE — `/signup` (`src/pages/SignupPage.jsx`)

### 6.1 Layout
Same two-column split as login. Left panel uses a different GSAP sequence.

```jsx
// src/pages/SignupPage.jsx
import SignupAnimation from '../components/auth/SignupAnimation'
import { useState }    from 'react'
import { Link }        from 'react-router-dom'

const ROLES    = ['Retail Analyst', 'Fund Manager', 'Research Intern', 'Other']
const SECTORS  = ['FMCG', 'IT', 'NBFC', 'Pharma', 'Auto', 'Real Estate', 'Infra', 'Energy']

export default function SignupPage() {
  const [name,     setName]     = useState('')
  const [email,    setEmail]    = useState('')
  const [org,      setOrg]      = useState('')
  const [password, setPassword] = useState('')
  const [confirm,  setConfirm]  = useState('')
  const [role,     setRole]     = useState('Retail Analyst')
  const [sectors,  setSectors]  = useState([])
  const [agreed,   setAgreed]   = useState(false)

  function toggleSector(s) {
    setSectors(prev =>
      prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]
    )
  }

  // Password strength 0–4
  const strength = password.length === 0 ? 0
    : password.length < 6  ? 1
    : password.length < 10 ? 2
    : password.length < 14 ? 3 : 4

  const strengthColors = ['', 'bg-erebus-red', 'bg-erebus-amber',
                          'bg-erebus-amber', 'bg-erebus-green']

  return (
    <div className="flex h-screen bg-erebus-bg">
      <SignupAnimation />

      <div className="flex-[0_0_45%] bg-erebus-surface
                      border-l border-[var(--erebus-border)]
                      flex items-center justify-center px-10 overflow-y-auto py-10">
        <div className="w-full max-w-sm">
          <h1 className="text-[28px] font-medium text-erebus-text-1 mb-1">
            Create your workspace
          </h1>
          <p className="text-[14px] text-erebus-text-2 mb-8">
            Free forever on the Starter plan
          </p>

          <form className="space-y-4">
            {/* Full name */}
            <div>
              <label className="block text-[13px] text-erebus-text-2 mb-1.5">
                Full name
              </label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                className="input-erebus w-full bg-erebus-bg text-erebus-text-1
                           border border-white/10 rounded-md px-4 py-3 text-[15px]
                           outline-none placeholder:text-erebus-text-3
                           focus:border-erebus-gold focus:ring-2
                           focus:ring-erebus-gold/10 transition-all"
                placeholder="Riya Sharma"
                required
              />
            </div>

            {/* Work email */}
            <div>
              <label className="block text-[13px] text-erebus-text-2 mb-1.5">
                Work email
              </label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="input-erebus w-full bg-erebus-bg text-erebus-text-1
                           border border-white/10 rounded-md px-4 py-3 text-[15px]
                           outline-none placeholder:text-erebus-text-3
                           focus:border-erebus-gold focus:ring-2
                           focus:ring-erebus-gold/10 transition-all"
                placeholder="you@firm.com"
                required
              />
            </div>

            {/* Organisation */}
            <div>
              <label className="block text-[13px] text-erebus-text-2 mb-1.5">
                Organisation <span className="text-erebus-text-3">(optional)</span>
              </label>
              <input
                type="text"
                value={org}
                onChange={e => setOrg(e.target.value)}
                className="input-erebus w-full bg-erebus-bg text-erebus-text-1
                           border border-white/10 rounded-md px-4 py-3 text-[15px]
                           outline-none placeholder:text-erebus-text-3
                           focus:border-erebus-gold focus:ring-2
                           focus:ring-erebus-gold/10 transition-all"
                placeholder="Leave blank if independent"
              />
            </div>

            {/* Password + strength meter */}
            <div>
              <label className="block text-[13px] text-erebus-text-2 mb-1.5">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="input-erebus w-full bg-erebus-bg text-erebus-text-1
                           border border-white/10 rounded-md px-4 py-3 text-[15px]
                           outline-none placeholder:text-erebus-text-3
                           focus:border-erebus-gold focus:ring-2
                           focus:ring-erebus-gold/10 transition-all"
                placeholder="••••••••"
                required
              />
              {/* 4-segment strength bar */}
              <div className="flex gap-1 mt-2">
                {[1, 2, 3, 4].map(seg => (
                  <div
                    key={seg}
                    className={`flex-1 h-1 rounded-full transition-colors duration-300
                      ${strength >= seg ? strengthColors[strength] : 'bg-white/[0.06]'}`}
                  />
                ))}
              </div>
            </div>

            {/* Confirm password */}
            <div>
              <label className="block text-[13px] text-erebus-text-2 mb-1.5">
                Confirm password
              </label>
              <input
                type="password"
                value={confirm}
                onChange={e => setConfirm(e.target.value)}
                className="input-erebus w-full bg-erebus-bg text-erebus-text-1
                           border border-white/10 rounded-md px-4 py-3 text-[15px]
                           outline-none placeholder:text-erebus-text-3
                           focus:border-erebus-gold focus:ring-2
                           focus:ring-erebus-gold/10 transition-all"
                placeholder="••••••••"
                required
              />
            </div>

            {/* Role selector */}
            <div>
              <label className="block text-[13px] text-erebus-text-2 mb-2">
                Your role
              </label>
              <div className="flex flex-wrap gap-2">
                {ROLES.map(r => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setRole(r)}
                    className={`px-3 py-1.5 rounded-full text-[13px] border transition-all
                      ${role === r
                        ? 'bg-[var(--erebus-gold-dim)] border-erebus-gold text-erebus-gold'
                        : 'bg-transparent border-white/10 text-erebus-text-2 hover:border-white/20'
                      }`}
                  >
                    {r}
                  </button>
                ))}
              </div>
            </div>

            {/* Sector chips */}
            <div>
              <label className="block text-[13px] text-erebus-text-2 mb-2">
                Sector interest <span className="text-erebus-text-3">(optional)</span>
              </label>
              <div className="flex flex-wrap gap-2">
                {SECTORS.map(s => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => toggleSector(s)}
                    className={`px-3 py-1.5 rounded-full text-[13px] border transition-all
                      ${sectors.includes(s)
                        ? 'border-erebus-gold text-erebus-gold'
                        : 'border-white/10 text-erebus-text-2 hover:border-white/20'
                      }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* TOS */}
            <label className="flex items-start gap-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={agreed}
                onChange={e => setAgreed(e.target.checked)}
                className="mt-0.5 accent-erebus-gold"
              />
              <span className="text-[13px] text-erebus-text-2">
                I agree to the{' '}
                <a href="#" className="text-erebus-gold hover:underline">
                  Terms of Service
                </a>{' '}
                and{' '}
                <a href="#" className="text-erebus-gold hover:underline">
                  Privacy Policy
                </a>
              </span>
            </label>

            {/* Submit */}
            <button
              type="submit"
              disabled={!agreed}
              className="w-full h-12 bg-erebus-gold text-erebus-bg rounded-md
                         text-[15px] font-semibold hover:bg-[#D4B55C]
                         active:scale-[0.98] transition-all duration-150
                         disabled:opacity-50"
            >
              Create account
            </button>
          </form>

          <p className="text-center text-[14px] text-erebus-text-2 mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-erebus-gold hover:underline">
              Sign in →
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
```

---

### 6.2 SIGNUP ANIMATION (`src/components/auth/SignupAnimation.jsx`)

```jsx
// src/components/auth/SignupAnimation.jsx
// GSAP sequence:
// Phase 1: Persona cards slide in (Retail Analyst / Fund Manager / Researcher)
// Phase 2: Research report builds line-by-line (typewriter)
// Phase 3: Confidence bars fill 0 → final values
// Phase 4: Comparison table materialises row by row
// Loop

import { useEffect, useRef } from 'react'

export default function SignupAnimation() {
  const ref = useRef(null)

  useEffect(() => {
    // GSAP timeline implementation here
  }, [])

  return (
    <div
      ref={ref}
      className="flex-[0_0_55%] relative bg-erebus-bg overflow-hidden
                 flex items-center justify-center"
    >
      {/* Persona cards — Phase 1 */}
      {[
        { label: 'Retail Analyst',  initials: 'RA' },
        { label: 'Fund Manager',    initials: 'FM' },
        { label: 'Researcher',      initials: 'RS' },
      ].map(p => (
        <div
          key={p.label}
          className="persona-card absolute opacity-0 flex items-center gap-3
                     bg-erebus-surface border border-[var(--erebus-border)]
                     rounded-xl px-4 py-3"
        >
          <div className="w-9 h-9 rounded-full bg-[var(--erebus-gold-dim)]
                          flex items-center justify-center
                          text-erebus-gold text-[12px] font-semibold">
            {p.initials}
          </div>
          <span className="text-[14px] text-erebus-text-1">{p.label}</span>
        </div>
      ))}

      {/* Research report — Phase 2 */}
      <div className="report-card absolute opacity-0 w-72 bg-erebus-surface
                      border border-[var(--erebus-border)] rounded-xl p-5">
        <p className="font-mono text-[10px] text-erebus-text-3 mb-3 tracking-[0.08em]">
          RESEARCH OUTPUT · TITAN COMPANY
        </p>
        <div className="text-[13px] text-erebus-text-2 leading-[1.8] space-y-1">
          {[
            'Revenue growth of 26% YoY driven by jewellery segment...',
            'EBITDA margin expanded 180bps to 11.4% in Q4 FY24...',
            'Management guided for 18-20% volume growth in FY25...',
          ].map((line, i) => (
            <p key={i} className="report-line opacity-0">{line}</p>
          ))}
        </div>
      </div>

      <p className="absolute bottom-5 left-1/2 -translate-x-1/2
                    font-mono text-[10px] text-erebus-text-3 tracking-[0.1em] whitespace-nowrap">
        EREBUS · RETRIEVAL & KNOWLEDGE · QUANTITATIVE CORE · NLP SIGNAL
      </p>
    </div>
  )
}
```

---

## 7. MAIN APP — `/app`

### 7.1 App Shell (`src/components/layout/AppShell.jsx`)

```jsx
// src/components/layout/AppShell.jsx
import { Outlet } from 'react-router-dom'
import Sidebar    from './Sidebar'
import TopBar     from './TopBar'

export default function AppShell() {
  return (
    <div className="flex h-screen bg-erebus-bg overflow-hidden">
      {/* Fixed sidebar: 240px */}
      <Sidebar />

      {/* Main area */}
      <div className="flex flex-col flex-1 overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
```

---

### 7.2 SIDEBAR (`src/components/layout/Sidebar.jsx`)

```jsx
// src/components/layout/Sidebar.jsx
import { NavLink }   from 'react-router-dom'
import { useState }  from 'react'

const NAV_ITEMS = [
  { icon: '💬', label: 'Chat',       to: '/app/chat'      },
  { icon: '📊', label: 'Scorecards', to: '/app/scorecard' },
  { icon: '⚖️', label: 'Compare',    to: '/app/compare'   },
  { icon: '📁', label: 'My Files',   to: '/app/files'     },
  { icon: '🕐', label: 'History',    to: '/app/history'   },
]

const RECENT_CHATS = [
  'HDFC Bank margin trajectory',
  'Titan vs Kalyan ROE comparison',
  'Asian Paints FY24 guidance',
  'Nifty IT sector risk analysis',
]

export default function Sidebar() {
  const [hoveredChat, setHoveredChat] = useState(null)

  return (
    <aside className="w-60 h-full bg-erebus-bg border-r border-white/[0.06]
                      flex flex-col shrink-0">
      {/* Logo */}
      <div className="px-4 py-4 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full border border-erebus-gold
                          bg-[var(--erebus-gold-dim)] flex items-center
                          justify-center font-serif text-erebus-gold text-base">
            E
          </div>
          <span className="font-serif text-[18px] text-erebus-text-1">EREBUS</span>
        </div>
        <p className="text-[12px] text-erebus-text-3 mt-1">My Research Workspace</p>
      </div>

      {/* Nav items */}
      <nav className="py-2">
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-2.5 h-9 px-3 mx-2 rounded-md text-[14px]
               transition-all duration-150
               ${isActive
                 ? 'bg-[var(--erebus-gold-dim)] text-erebus-gold'
                 : 'text-erebus-text-2 hover:bg-erebus-surface hover:text-erebus-text-1'
               }`
            }
          >
            <span className="text-[16px]">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Recent chats */}
      <div className="flex-1 overflow-y-auto">
        <p className="px-5 pt-4 pb-2 text-[10px] font-mono text-erebus-text-3
                      tracking-[0.1em] uppercase">
          Recent
        </p>
        {RECENT_CHATS.map((chat, i) => (
          <div
            key={i}
            className="flex items-center h-8 px-5 text-[13px] text-erebus-text-2
                       cursor-pointer hover:text-erebus-text-1 group"
            onMouseEnter={() => setHoveredChat(i)}
            onMouseLeave={() => setHoveredChat(null)}
          >
            <span className="truncate flex-1">{chat}</span>
            {hoveredChat === i && (
              <span className="text-erebus-text-3 hover:text-erebus-red text-[11px]">
                🗑
              </span>
            )}
          </div>
        ))}
      </div>

      {/* User info */}
      <div className="px-4 py-4 border-t border-white/[0.06]
                      flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-full bg-[var(--erebus-gold-dim)]
                        flex items-center justify-center
                        text-erebus-gold text-[12px] font-semibold shrink-0">
          RK
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[13px] text-erebus-text-1 truncate">Rohan Kumar</p>
          <p className="text-[11px] text-erebus-text-3 truncate">rohan@firm.com</p>
        </div>
        <button className="text-erebus-text-3 hover:text-erebus-text-2 text-[18px]">
          ⚙
        </button>
      </div>
    </aside>
  )
}
```

---

### 7.3 TOP BAR (`src/components/layout/TopBar.jsx`)

```jsx
// src/components/layout/TopBar.jsx
import { useLocation, useNavigate } from 'react-router-dom'

const PAGE_TITLES = {
  '/app/chat':      'Chat',
  '/app/scorecard': 'Scorecards',
  '/app/compare':   'Compare',
  '/app/files':     'My Files',
  '/app/history':   'History',
}

export default function TopBar() {
  const { pathname } = useLocation()
  const navigate     = useNavigate()
  const title        = PAGE_TITLES[pathname] ?? 'EREBUS'

  return (
    <div className="h-14 flex items-center justify-between px-6
                    border-b border-white/[0.06] shrink-0">
      <h2 className="text-[16px] font-medium text-erebus-text-1">{title}</h2>

      <div className="flex items-center gap-3">
        <button className="text-erebus-text-3 hover:text-erebus-text-1 text-[20px]">
          🔔
        </button>
        <button
          onClick={() => navigate('/app/chat')}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[13px]
                     text-erebus-gold bg-[var(--erebus-gold-dim)]
                     border border-erebus-gold/30 hover:bg-erebus-gold/20
                     transition-colors duration-150"
        >
          + New Chat
        </button>
      </div>
    </div>
  )
}
```

---

## 8. CHAT PAGE — `/app/chat` (`src/pages/app/ChatPage.jsx`)

```jsx
// src/pages/app/ChatPage.jsx
import { useState, useRef, useEffect } from 'react'
import FileUploadZone   from '../../components/chat/FileUploadZone'
import SuggestionChips  from '../../components/chat/SuggestionChips'
import MessageThread    from '../../components/chat/MessageThread'
import ChatInput        from '../../components/chat/ChatInput'
import ContextPanel     from '../../components/layout/ContextPanel'

export default function ChatPage() {
  const [messages,      setMessages]      = useState([])
  const [panelOpen,     setPanelOpen]     = useState(false)
  const [activeSources, setActiveSources] = useState([])
  const [thinking,      setThinking]      = useState(false)

  function handleSend(text) {
    const userMsg = { role: 'user', text }
    setMessages(prev => [...prev, userMsg])
    setThinking(true)
    // Call EREBUS API — on response:
    setTimeout(() => {
      setMessages(prev => [...prev, {
        role:    'assistant',
        text:    'Based on HDFC Bank's Q4 FY24 annual report, net interest margin compressed 28bps YoY...',
        sources: ['Annual Report FY24 · p.47', 'Q4 Concall · p.12'],
      }])
      setThinking(false)
    }, 2000)
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex h-full overflow-hidden">
      {/* Chat area */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {isEmpty ? (
          // Empty state
          <div className="flex-1 flex flex-col items-center justify-center px-6 gap-6">
            <div className="w-12 h-12 rounded-full border-2 border-erebus-gold
                            bg-[var(--erebus-gold-dim)] flex items-center
                            justify-center font-serif text-erebus-gold text-2xl">
              E
            </div>
            <div className="text-center">
              <h2 className="font-serif text-[28px] text-erebus-text-1 mb-2">
                What would you like to research?
              </h2>
              <p className="text-[15px] text-erebus-text-2">
                Ask about any Indian listed company — financials, guidance, risk, or peer comparison.
              </p>
            </div>
            <SuggestionChips onSelect={handleSend} />
            <FileUploadZone />
          </div>
        ) : (
          <MessageThread
            messages={messages}
            thinking={thinking}
            onSourceClick={sources => {
              setActiveSources(sources)
              setPanelOpen(true)
            }}
          />
        )}

        {/* Input */}
        <ChatInput onSend={handleSend} />
      </div>

      {/* Context panel */}
      <ContextPanel
        open={panelOpen}
        sources={activeSources}
        onClose={() => setPanelOpen(false)}
      />
    </div>
  )
}
```

---

### 8.1 SUGGESTION CHIPS (`src/components/chat/SuggestionChips.jsx`)

```jsx
// src/components/chat/SuggestionChips.jsx
const SUGGESTIONS = [
  'Analyse HDFC Bank\'s margin trajectory',
  'Compare Titan vs Kalyan Jewellers ROE',
  'Management guidance hits for Asian Paints Q4',
  'Risk score for Adani Enterprises',
  'Top 3 pharma companies by FCF conversion',
]

export default function SuggestionChips({ onSelect }) {
  return (
    <div className="flex gap-2.5 overflow-x-auto pb-1 max-w-2xl w-full
                    scrollbar-none">
      {SUGGESTIONS.map(s => (
        <button
          key={s}
          onClick={() => onSelect(s)}
          className="px-4 py-2.5 rounded-full text-[14px] text-erebus-text-2
                     bg-erebus-surface border border-white/[0.08]
                     hover:border-erebus-gold hover:text-erebus-text-1
                     whitespace-nowrap transition-all duration-200 shrink-0"
        >
          {s}
        </button>
      ))}
    </div>
  )
}
```

---

### 8.2 FILE UPLOAD ZONE (`src/components/chat/FileUploadZone.jsx`)

```jsx
// src/components/chat/FileUploadZone.jsx
// Uses react-dropzone: npm install react-dropzone

import { useDropzone } from 'react-dropzone'

export default function FileUploadZone({ onFiles }) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: onFiles,
    accept: {
      'application/pdf':  ['.pdf'],
      'text/plain':       ['.txt'],
      'application/json': ['.json'],
      'text/csv':         ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
  })

  return (
    <div
      {...getRootProps()}
      className={`max-w-2xl w-full cursor-pointer rounded-xl p-6 text-center
                  border-[1.5px] border-dashed transition-all duration-200
                  ${isDragActive
                    ? 'border-erebus-gold/40 bg-[var(--erebus-gold-glow)]'
                    : 'border-white/10 hover:border-erebus-gold/40 hover:bg-[var(--erebus-gold-glow)]'
                  }`}
    >
      <input {...getInputProps()} />
      <div className="text-[24px] text-erebus-text-3 mb-2">☁</div>
      <p className="text-[14px] text-erebus-text-3 mb-1">
        Drop annual reports, transcripts, or data files here
      </p>
      <p className="text-[12px] text-erebus-text-3/60">
        PDF, XLSX, CSV, TXT, JSON — up to 50MB per file
      </p>
    </div>
  )
}
```

---

### 8.3 CHAT INPUT (`src/components/chat/ChatInput.jsx`)

```jsx
// src/components/chat/ChatInput.jsx
import { useState, useRef } from 'react'

export default function ChatInput({ onSend }) {
  const [text,        setText]        = useState('')
  const [attachments, setAttachments] = useState([])
  const textareaRef                   = useRef(null)

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleSend() {
    if (!text.trim()) return
    onSend(text.trim())
    setText('')
    setAttachments([])
  }

  // Auto-resize textarea
  function handleChange(e) {
    setText(e.target.value)
    const ta = textareaRef.current
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 200) + 'px'
  }

  return (
    <div className="px-6 pb-4 pt-2"
         style={{ background: 'linear-gradient(transparent, #0D0F14 40%)' }}>
      {/* Attachment preview */}
      {attachments.length > 0 && (
        <div className="flex gap-2 mb-2 flex-wrap">
          {attachments.map((f, i) => (
            <div
              key={i}
              className="flex items-center gap-2 px-2.5 py-1.5 rounded-md text-[13px]
                         text-erebus-text-2 bg-erebus-surface-2 border border-white/[0.08]"
            >
              <span>📎</span>
              <span className="max-w-[140px] truncate">{f.name}</span>
              <button
                onClick={() => setAttachments(prev => prev.filter((_, j) => j !== i))}
                className="text-erebus-text-3 hover:text-erebus-red ml-1"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input box */}
      <div className="bg-erebus-surface border border-white/10 rounded-[14px]
                      px-4 py-3 focus-within:border-erebus-gold/40
                      transition-colors duration-200">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder="Ask about any listed Indian company..."
          className="w-full bg-transparent text-[15px] text-erebus-text-1
                     placeholder:text-erebus-text-3 outline-none resize-none
                     max-h-[200px] leading-[1.6]"
        />

        {/* Toolbar */}
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center gap-3">
            {/* Attachment */}
            <button className="text-erebus-text-3 hover:text-erebus-text-2
                               text-[20px] transition-colors">
              📎
            </button>
            {/* Company autocomplete trigger */}
            <button className="text-[12px] font-mono text-erebus-text-3
                               hover:text-erebus-text-2 transition-colors
                               border border-white/[0.08] rounded px-2 py-0.5">
              + Company
            </button>
          </div>

          {/* Send */}
          <button
            onClick={handleSend}
            disabled={!text.trim()}
            className="w-9 h-9 rounded-full bg-erebus-gold flex items-center
                       justify-center text-erebus-bg text-[18px]
                       hover:bg-[#D4B55C] active:scale-[0.96]
                       disabled:bg-erebus-gold/20 disabled:cursor-not-allowed
                       transition-all duration-150"
          >
            →
          </button>
        </div>
      </div>

      <p className="text-center text-[12px] text-erebus-text-3/60 mt-2">
        EREBUS cites every claim. Responses are for research only — not investment advice.
      </p>
    </div>
  )
}
```

---

### 8.4 MESSAGE THREAD (`src/components/chat/MessageThread.jsx`)

```jsx
// src/components/chat/MessageThread.jsx
import { useEffect, useRef } from 'react'
import AgentMessage          from './AgentMessage'

export default function MessageThread({ messages, thinking, onSourceClick }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking])

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
      {messages.map((msg, i) => (
        msg.role === 'user' ? (
          // User bubble — right aligned
          <div key={i} className="flex justify-end">
            <div>
              <div className="max-w-[70%] px-4 py-3 rounded-[12px_12px_2px_12px]
                              bg-[var(--erebus-gold-dim)] border border-erebus-gold/20
                              text-[15px] text-erebus-text-1 leading-[1.7]">
                {msg.text}
              </div>
              <p className="text-[11px] text-erebus-text-3 mt-1 text-right">Just now</p>
            </div>
          </div>
        ) : (
          <AgentMessage
            key={i}
            message={msg}
            onSourceClick={onSourceClick}
          />
        )
      ))}

      {/* Thinking state */}
      {thinking && (
        <div className="flex items-start gap-3">
          <div className="w-7 h-7 rounded-full border border-erebus-gold
                          bg-[var(--erebus-gold-dim)] flex items-center
                          justify-center font-serif text-erebus-gold text-sm shrink-0">
            E
          </div>
          <div className="flex flex-col gap-1 pt-1">
            <div className="flex items-center gap-1.5 px-3 py-2
                            bg-erebus-surface border border-[var(--erebus-border)]
                            rounded-lg">
              {[0, 1, 2].map(i => (
                <span
                  key={i}
                  className="w-1.5 h-1.5 rounded-full bg-erebus-gold
                             animate-pulse-dot"
                  style={{ animationDelay: `${i * 0.2}s` }}
                />
              ))}
            </div>
            <p className="text-[11px] font-mono text-erebus-text-3 px-1">
              Retrieving context → Computing ratios → Generating insight
            </p>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
```

---

### 8.5 AGENT MESSAGE (`src/components/chat/AgentMessage.jsx`)

```jsx
// src/components/chat/AgentMessage.jsx
// Renders: source pills, main text, structured data blocks, follow-up chips, action row

export default function AgentMessage({ message, onSourceClick }) {
  const { text, sources, table, scorecard, guidanceTracker, comparisonTable } = message

  return (
    <div className="flex items-start gap-3">
      {/* Avatar */}
      <div className="w-7 h-7 rounded-full border border-erebus-gold
                      bg-[var(--erebus-gold-dim)] flex items-center
                      justify-center font-serif text-erebus-gold text-sm shrink-0 mt-0.5">
        E
      </div>

      <div className="flex-1 min-w-0 space-y-3">
        {/* (a) Source pills */}
        {sources?.length > 0 && (
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
            {sources.map((src, i) => (
              <button
                key={i}
                onClick={() => onSourceClick(sources)}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-md
                           text-[12px] font-mono text-erebus-text-2 shrink-0
                           bg-erebus-surface-2 border border-white/[0.08]
                           hover:border-erebus-gold hover:text-erebus-gold
                           transition-all duration-150"
              >
                📄 {src}
              </button>
            ))}
          </div>
        )}

        {/* (b) Main text */}
        <p className="text-[15px] text-erebus-text-1 leading-[1.75]">{text}</p>

        {/* (c) Financial table */}
        {table && (
          <div className="bg-erebus-surface border border-white/[0.06]
                          rounded-lg overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="bg-white/[0.04]">
                  {table.headers.map(h => (
                    <th key={h} className="px-4 py-2.5 text-left text-[12px]
                                           font-mono text-erebus-text-3 tracking-[0.05em]
                                           font-normal">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.rows.map((row, i) => (
                  <tr key={i}
                      className={i % 2 === 1 ? 'bg-white/[0.02]' : ''}>
                    {row.map((cell, j) => (
                      <td
                        key={j}
                        className={`px-4 py-2.5 text-[14px]
                          ${typeof cell === 'string' && cell.startsWith('+')
                              ? 'text-erebus-green'
                            : typeof cell === 'string' && cell.startsWith('-')
                              ? 'text-erebus-red'
                              : 'text-erebus-text-1'
                          }`}
                      >
                        {cell === 'HIGH'   && <span className="px-2 py-0.5 rounded-full text-[11px] bg-erebus-green/10 text-erebus-green">HIGH</span>}
                        {cell === 'MED'    && <span className="px-2 py-0.5 rounded-full text-[11px] bg-erebus-amber/10 text-erebus-amber">MED</span>}
                        {cell === 'LOW'    && <span className="px-2 py-0.5 rounded-full text-[11px] bg-erebus-red/10 text-erebus-red">LOW</span>}
                        {!['HIGH','MED','LOW'].includes(cell) && cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* (d) Follow-up chips */}
        <div className="flex gap-2 flex-wrap">
          {[
            'Dig deeper into risk factors →',
            'Compare with peers →',
            'Show 4-quarter trend →',
          ].map(chip => (
            <button
              key={chip}
              className="px-3.5 py-1.5 rounded-full text-[13px]
                         text-erebus-text-2 bg-erebus-surface
                         border border-white/[0.08]
                         hover:border-erebus-gold hover:text-erebus-text-1
                         transition-all duration-200"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* (e) Action row */}
        <div className="flex items-center gap-4">
          {['📋 Copy', '🔄 Regenerate', '📂 Sources', '👍', '👎'].map(a => (
            <button
              key={a}
              className="text-[13px] text-erebus-text-3
                         hover:text-erebus-text-2 transition-colors"
            >
              {a}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
```

---

### 8.6 CONTEXT PANEL (`src/components/layout/ContextPanel.jsx`)

```jsx
// src/components/layout/ContextPanel.jsx
export default function ContextPanel({ open, sources, onClose }) {
  return (
    <div
      className={`h-full border-l border-white/[0.06] bg-erebus-bg
                  flex flex-col shrink-0 transition-all duration-[280ms] ease-out
                  ${open ? 'w-80' : 'w-0 overflow-hidden'}`}
    >
      {open && (
        <>
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4
                          border-b border-white/[0.06]">
            <h3 className="text-[14px] font-medium text-erebus-text-1">Sources</h3>
            <button
              onClick={onClose}
              className="text-erebus-text-3 hover:text-erebus-text-1
                         text-[20px] transition-colors"
            >
              ×
            </button>
          </div>

          {/* Source cards */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
            {sources.map((src, i) => (
              <div
                key={i}
                className="bg-erebus-surface rounded-lg border
                           border-[var(--erebus-border)] p-4"
              >
                <div className="flex items-start gap-2 mb-2">
                  <span className="text-[16px]">📄</span>
                  <div>
                    <p className="text-[13px] font-medium text-erebus-text-1">
                      {src.split(' · ')[0]}
                    </p>
                    <p className="text-[12px] text-erebus-text-2">{src}</p>
                  </div>
                  <span className="ml-auto text-[11px] px-2 py-0.5 rounded-full
                                   bg-erebus-green/10 text-erebus-green shrink-0">
                    HIGH
                  </span>
                </div>
                {/* Highlighted excerpt */}
                <div className="border-l-[3px] border-erebus-gold pl-3
                                bg-[var(--erebus-gold-glow)] rounded-r py-1">
                  <p className="text-[12px] text-erebus-text-2 leading-[1.6]">
                    "Net interest margin stood at 3.63% for Q4 FY24, compared
                    to 3.91% in Q4 FY23, reflecting merger-related cost pressures..."
                  </p>
                </div>
                <button className="text-[12px] text-erebus-gold hover:underline mt-2 block">
                  View full document →
                </button>
              </div>
            ))}
          </div>

          {/* Data Confidence Index */}
          <div className="px-4 pb-4 border-t border-white/[0.06] pt-4">
            <p className="text-[12px] text-erebus-text-3 mb-3">Data Confidence Index</p>
            {[
              { label: 'Source quality',         score: 92 },
              { label: 'Coverage completeness',  score: 78 },
              { label: 'Temporal freshness',     score: 85 },
              { label: 'Cross-validation',       score: 71 },
            ].map(item => (
              <div key={item.label} className="flex items-center gap-2.5 mb-2">
                <span className="text-[12px] text-erebus-text-3 w-36 shrink-0">
                  {item.label}
                </span>
                <div className="flex-1 h-1 bg-white/[0.06] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-erebus-green rounded-full transition-all duration-700"
                    style={{ width: item.score + '%' }}
                  />
                </div>
                <span className="font-mono text-[11px] text-erebus-text-2 w-7 text-right">
                  {item.score}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
```

---

## 9. HISTORY PAGE (`src/pages/app/HistoryPage.jsx`)

```jsx
// src/pages/app/HistoryPage.jsx
import { useState } from 'react'

const FILTERS = ['All', 'Scorecards', 'Comparisons', 'Q&A', 'File Uploads']

const HISTORY = [
  { title: 'HDFC Bank NIM Analysis',        tags: ['HDFCBANK'], preview: 'Net interest margin compressed 28bps YoY...', ts: '2h ago'  },
  { title: 'Titan vs Kalyan ROE Compare',   tags: ['TITAN','KALYANKJIL'], preview: 'Titan leads on ROE at 31.2% vs 18.4%...', ts: '5h ago' },
  { title: 'Asian Paints Guidance Tracker', tags: ['ASIANPAINT'], preview: 'Management guided 12-14% volume growth...', ts: '1d ago'  },
  { title: 'Adani Enterprises Risk Score',  tags: ['ADANIENT'], preview: 'CAS score of 42 — elevated governance risk...', ts: '2d ago'  },
  { title: 'Nifty IT Sector Scan',          tags: ['INFY','TCS','WIPRO'], preview: 'All three names showing margin recovery...', ts: '3d ago' },
  { title: 'Sun Pharma Scorecard',          tags: ['SUNPHARMA'], preview: 'Strong FCF conversion of 0.87x EBITDA...', ts: '4d ago'  },
]

export default function HistoryPage() {
  const [filter,  setFilter]  = useState('All')
  const [search,  setSearch]  = useState('')

  const filtered = HISTORY.filter(h =>
    h.title.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="p-6 h-full overflow-y-auto">
      {/* Search */}
      <div className="relative mb-4">
        <span className="absolute left-4 top-1/2 -translate-y-1/2
                         text-erebus-text-3 text-[16px]">🔍</span>
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search past research..."
          className="w-full bg-erebus-surface border border-[var(--erebus-border)]
                     rounded-lg pl-10 pr-4 py-2.5 text-[15px] text-erebus-text-1
                     placeholder:text-erebus-text-3 outline-none
                     focus:border-erebus-gold/40 transition-colors"
        />
      </div>

      {/* Filter chips */}
      <div className="flex gap-2 mb-6">
        {FILTERS.map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3.5 py-1.5 rounded-full text-[13px] border
                        transition-all duration-150
                        ${filter === f
                          ? 'bg-[var(--erebus-gold-dim)] border-erebus-gold text-erebus-gold'
                          : 'border-white/[0.08] text-erebus-text-2 hover:border-white/20'
                        }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* History grid */}
      <div className="grid grid-cols-3 gap-4">
        {filtered.map((item, i) => (
          <div
            key={i}
            className="bg-erebus-surface border border-[var(--erebus-border)]
                       rounded-xl p-5 cursor-pointer
                       hover:border-erebus-gold/25 hover:bg-erebus-surface-2
                       transition-all duration-200"
          >
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-[14px] font-medium text-erebus-text-1 leading-[1.4]">
                {item.title}
              </h3>
              <span className="text-[11px] text-erebus-text-3 shrink-0 ml-2">{item.ts}</span>
            </div>
            <div className="flex flex-wrap gap-1.5 mb-3">
              {item.tags.map(tag => (
                <span
                  key={tag}
                  className="font-mono text-[11px] text-erebus-gold
                             bg-[var(--erebus-gold-dim)] px-2 py-0.5 rounded-md"
                >
                  {tag}
                </span>
              ))}
            </div>
            <p className="text-[13px] text-erebus-text-3 leading-[1.6] line-clamp-2">
              {item.preview}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
```

---

## 10. RESPONSIVE BREAKPOINTS

```jsx
// Tailwind breakpoint usage across the app

// Sidebar: full on desktop → icon-only on tablet → bottom tab bar on mobile
// Use: sm:hidden md:w-12 lg:w-60

// Chat context panel: visible on desktop → hidden by default on tablet
// Use: hidden xl:flex

// Feature grid: 3-col → 2-col → 1-col
// Use: grid-cols-1 md:grid-cols-2 lg:grid-cols-3

// Hero H1: 72px → 48px
// Use: text-[48px] lg:text-[72px]

// Pricing grid: 1-col → 3-col
// Use: grid-cols-1 md:grid-cols-3
```

### Mobile Tab Bar (`src/components/layout/MobileTabBar.jsx`)

```jsx
// src/components/layout/MobileTabBar.jsx
import { NavLink } from 'react-router-dom'

const TABS = [
  { icon: '💬', label: 'Chat',      to: '/app/chat'      },
  { icon: '📊', label: 'Scorecard', to: '/app/scorecard' },
  { icon: '⚖️', label: 'Compare',   to: '/app/compare'   },
  { icon: '📁', label: 'Files',     to: '/app/files'     },
  { icon: '🕐', label: 'History',   to: '/app/history'   },
]

export default function MobileTabBar() {
  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 h-[60px]
                    bg-erebus-bg border-t border-white/[0.06]
                    flex items-center justify-around
                    pb-[env(safe-area-inset-bottom)] z-50">
      {TABS.map(tab => (
        <NavLink
          key={tab.to}
          to={tab.to}
          className={({ isActive }) =>
            `flex flex-col items-center gap-0.5
             ${isActive ? 'text-erebus-gold' : 'text-erebus-text-3'}`
          }
        >
          <span className="text-[22px]">{tab.icon}</span>
          <span className="text-[10px]">{tab.label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
```

---

## 11. MICROINTERACTIONS & ANIMATIONS

### Loading States

```jsx
// 3-dot thinking animation
<div className="flex gap-1">
  {[0, 1, 2].map(i => (
    <span
      key={i}
      className="w-2 h-2 rounded-full bg-erebus-gold animate-pulse-dot"
      style={{ animationDelay: `${i * 0.2}s` }}
    />
  ))}
</div>

// Ticker-style thinking label (cycles through states)
// Implement with useState + useInterval cycling:
// 'Retrieving context...' → 'Computing ratios...' → 'Generating insight...'

// File upload radial progress
<div className="relative w-10 h-10">
  <svg className="rotate-[-90deg]" viewBox="0 0 36 36">
    <circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="3" />
    <circle
      cx="18" cy="18" r="15.9"
      fill="none" stroke="#C9A84C" strokeWidth="3"
      strokeDasharray={`${progress} 100`}
      strokeLinecap="round"
    />
  </svg>
  <span className="absolute inset-0 flex items-center justify-center
                   font-mono text-[10px] text-erebus-gold">
    {progress}%
  </span>
</div>
```

### Page Route Transitions

```jsx
// Wrap <Outlet /> in a transition wrapper
// Use framer-motion or CSS class toggling:

// Initial: opacity-0 translate-y-2
// Enter:   opacity-100 translate-y-0 transition-all duration-[250ms]
```

### Sidebar Collapse (Tablet)

```jsx
// Tailwind + CSS transition:
<aside className={`h-full bg-erebus-bg border-r border-white/[0.06]
  transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]
  ${collapsed ? 'w-12' : 'w-60'}`}>
```

---

## 12. TECH STACK (FRONTEND ONLY)

| Category      | Choice                           | Reason                         |
|---------------|----------------------------------|--------------------------------|
| Framework     | React 18 + Vite                  | Fast HMR, ecosystem            |
| Routing       | React Router v6                  | File-based routing             |
| Styling       | Tailwind CSS v3 + CSS variables  | Utility + theming              |
| Animations    | GSAP + ScrollTrigger             | Login page + landing           |
| State         | Zustand                          | Lightweight global state       |
| Data fetching | React Query (TanStack)           | Caching + loading states       |
| Charts        | Recharts                         | Lightweight, React-native      |
| File handling | react-dropzone                   | Upload UX                      |
| Icons         | Lucide React                     | Clean icon set                 |
| Fonts         | DM Serif Display + Inter + JetBrains Mono via Google Fonts |

### Install Command

```bash
npm create vite@latest erebus-app -- --template react
cd erebus-app
npm install react-router-dom gsap zustand @tanstack/react-query \
  recharts react-dropzone lucide-react
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

---

## 13. COMPONENT LIBRARY

All components go in `src/components/` — **all files use `.jsx`, no `.tsx`**:

```
src/
├── components/
│   ├── ui/
│   │   ├── Button.jsx       (variants: primary, ghost, danger — plain props)
│   │   ├── Input.jsx        (variants: default, search)
│   │   ├── Badge.jsx        (variants: gold, blue, green, red, amber)
│   │   ├── Card.jsx         (variants: default, elevated, interactive)
│   │   ├── Chip.jsx         (variants: default, selected, company-tag)
│   │   ├── Tooltip.jsx
│   │   ├── Modal.jsx
│   │   ├── Spinner.jsx
│   │   └── Divider.jsx
│   ├── layout/
│   │   ├── Sidebar.jsx
│   │   ├── TopBar.jsx
│   │   ├── AppShell.jsx
│   │   ├── ContextPanel.jsx
│   │   └── MobileTabBar.jsx
│   ├── chat/
│   │   ├── MessageThread.jsx
│   │   ├── UserMessage.jsx
│   │   ├── AgentMessage.jsx
│   │   ├── SourcePills.jsx
│   │   ├── ChatInput.jsx
│   │   ├── FileUploadZone.jsx
│   │   ├── SuggestionChips.jsx
│   │   └── blocks/
│   │       ├── FinancialTable.jsx
│   │       ├── ScorecardCard.jsx
│   │       ├── GuidanceTracker.jsx
│   │       └── ComparisonTable.jsx
│   ├── landing/
│   │   ├── Navbar.jsx
│   │   ├── Hero.jsx
│   │   ├── ProblemStatement.jsx
│   │   ├── FeatureGrid.jsx
│   │   ├── ArchDiagram.jsx
│   │   ├── Testimonials.jsx
│   │   └── Pricing.jsx
│   └── auth/
│       ├── LoginAnimation.jsx
│       └── SignupAnimation.jsx
├── pages/
│   ├── LandingPage.jsx
│   ├── LoginPage.jsx
│   ├── SignupPage.jsx
│   └── app/
│       ├── ChatPage.jsx
│       ├── ScorecardPage.jsx
│       ├── ComparePage.jsx
│       ├── HistoryPage.jsx
│       └── FilesPage.jsx
├── store/
│   └── useAppStore.js       (Zustand — no types needed, plain JS object)
├── hooks/
│   ├── useChat.js
│   └── useCompany.js
├── App.jsx
├── main.jsx
└── index.css
```

### Example Zustand Store (`src/store/useAppStore.js`)

```js
// src/store/useAppStore.js
import { create } from 'zustand'

const useAppStore = create((set) => ({
  // Chat
  messages:        [],
  thinking:        false,
  contextOpen:     false,
  activeSources:   [],

  // Actions
  addMessage:      (msg)     => set(state => ({ messages: [...state.messages, msg] })),
  setThinking:     (bool)    => set({ thinking: bool }),
  openContext:     (sources) => set({ contextOpen: true, activeSources: sources }),
  closeContext:    ()        => set({ contextOpen: false, activeSources: [] }),
  clearMessages:   ()        => set({ messages: [] }),
}))

export default useAppStore
```

### Example Button Component (`src/components/ui/Button.jsx`)

```jsx
// src/components/ui/Button.jsx
// No TypeScript — plain props object, no PropTypes required (optional)

export default function Button({
  children,
  variant  = 'primary',
  size     = 'md',
  disabled = false,
  loading  = false,
  onClick,
  className = '',
  ...rest
}) {
  const base = 'inline-flex items-center justify-center gap-2 font-medium rounded-md transition-all duration-150 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed'

  const variants = {
    primary: 'bg-erebus-gold text-erebus-bg hover:bg-[#D4B55C]',
    ghost:   'border border-white/[0.15] text-erebus-text-1 hover:border-erebus-gold hover:text-erebus-gold',
    danger:  'bg-erebus-red text-white hover:bg-[#D94F4F]',
  }

  const sizes = {
    sm: 'text-[13px] px-3 py-1.5',
    md: 'text-[14px] px-[18px] py-2',
    lg: 'text-[16px] px-7 py-[14px]',
  }

  return (
    <button
      disabled={disabled || loading}
      onClick={onClick}
      className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
      {...rest}
    >
      {loading
        ? <span className="w-4 h-4 border-2 border-current/30 border-t-current rounded-full animate-spin" />
        : children
      }
    </button>
  )
}
```

---

*End of EREBUS React + Tailwind Specification — all `.tsx` → `.jsx`, all TypeScript removed.*
