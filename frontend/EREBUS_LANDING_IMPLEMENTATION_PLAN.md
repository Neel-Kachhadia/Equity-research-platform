# EREBUS Landing Page — Implementation Plan
## React + Tailwind CSS | Terminal-Grade Institutional Design

---

## 🎯 Project Overview
Transform existing landing page into **EREBUS** — Bloomberg Terminal aesthetic for equity research. Dark void background with gold accents, serif/mono typography mix, data-rich components.

**Target Audience:** Serious analysts who can't justify $24K/year Bloomberg subscription  
**Design Philosophy:** Precision instruments, war room authority, institutional credibility

---

## 📐 Design System Specifications

### Color Palette (Tailwind Config)
```javascript
colors: {
  // Backgrounds
  'erebus-void': '#0D0F14',       // Primary bg
  'erebus-surface': '#13161E',    // Panels & lifted elements
  'erebus-depth': '#1A1D26',      // Deepest surfaces
  
  // Brand
  'erebus-gold': '#C9A84C',       // CTAs, active states, logo
  'erebus-gold-light': '#D4B560', // Hover states
  
  // Functional
  'erebus-green': '#3ECF8E',      // Gains, positive signals
  'erebus-red': '#E55C5C',        // Losses, risk flags
  'erebus-amber': '#F0A429',      // Warnings, guidance misses
  'erebus-blue': '#4A8FE7',       // Sources, links, citations
  
  // Text
  'erebus-cream': '#F0EDE6',      // Primary text (warm cream)
  'erebus-secondary': '#8B8E99',  // Secondary info
  'erebus-muted': '#545769',      // Timestamps, muted content
}
```

### Typography Stack
```css
/* Headings - Institutional Authority */
font-family: 'DM Serif Display', serif;
/* Use italic for emotional punch on hero */
font-style: italic;

/* Body & UI - Clean Modern */
font-family: 'Inter', sans-serif;

/* Tickers, Scores, Terminal Labels */
font-family: 'JetBrains Mono', monospace;
letter-spacing: 0.05em; /* Terminal feel */
```

### Spacing & Sizing
```
Section Padding:  2rem (mobile) → 4rem (tablet) → 8rem (desktop)
Component Gap:    1.5rem
Border Radius:    8px (subtle, not rounded)
Border Color:     rgba(255, 255, 255, 0.07) (whisper lines)
Gold Glow:        rgba(201, 168, 76, 0.08) (behind active elements)
```

---

## 🏗️ Landing Page Structure

### **1. Hero Section: "Bloomberg Terminal for India"**
**Location:** Above fold | Full viewport  
**Purpose:** Establish authority, hook analysts

**Components:**
- Animated hero headline (DM Serif, italic)
  - "Institutional-grade"
  - "research analytics"
  - "₹0 per month"
- Subheadline in cream text
- Two CTAs: "Start Free" (gold bg) + "See Feature Tour" (gold outline)
- Particle field animation (subtle data flowing)
- Terminal-style scroll indicator (chevron bouncing down)

**Design Notes:**
- No heavy video background (unlike NeuroFin)
- Keep dark void as bg, let typography be the hero
- Particle field = live data concept
- Gold glows subtly behind particle nodes

**Copywriting Angle:**
> "Bloomberg Terminal meets AI — institutional-grade equity research, without the $24K price tag."

---

### **2. Problem Section: "Why Analysts Struggle"**
**Location:** Post hero scroll  
**Purpose:** Validate pain points

**Components:**
- Three constraint cards in a grid:
  1. **Cost** — "₹2L/year" (red) vs "EREBUS: ₹0-5L"
  2. **Data Silos** — Multiple tools, scattered research
  3. **Speed** — Reports take weeks, AI can do hours

**Design:**
- Cards: `border-t: 2px solid #C9A84C` (gold top border only)
- `bg-erebus-surface` with `border: 1px rgba(255,255,255,0.07)`
- No shadow, glass aesthetic
- Icon in mono font (ticker-style label) above headline

**Animation:**
- Stagger fade-in on scroll
- Gold border grows from left on hover

---

### **3. Feature Showcase: "Terminal Interface Walkthrough"**
**Location:** Main value communication  
**Purpose:** Show the product in action

**Components:**
- Horizontal scrolling feature carousel (like NeuroFin's FeatureScenesSection)
- 4-5 scenes showing key workflows:
  1. **Watchlist** — Add stocks, see live scoring
  2. **Research Dashboard** — AI-generated summaries + source links
  3. **Comparative Analysis** — Side-by-side company metrics
  4. **Alert System** — Real-time flags for news, earnings misses
  5. **Citation Engine** — Every claim links to source

**Design Per Scene:**
```
[Number] 01
[Mono Label] WATCHLIST
[Serif Headline] Real-time, 
                  precision scoring.
[Chips/Tags]: "AI-scored" "Sources cited" "30-sec insights"
[Screenshot] — Terminal-style dashboard
```

**Animation:**
- Pinned scroll with horizontal drag
- Image + content fade in as scene enters viewport
- Mono number counter (01 → 05) animates per scene

---

### **4. Credibility Section: "Institutional Trust"**
**Location:** After features  
**Purpose:** Build authority

**Components:**
- Three trust indicators (vertical aligned):
  1. **Sources** — "10K+ financial documents indexed"
  2. **Accuracy** — "94.2% fact-check rate" (large mono number)
  3. **Analysts** — "Built by researchers, coded by ex-Stripe engineers"

**Design:**
- Left-aligned headline in serif: "Built for professionals."
- Each indicator: small mono label → large serif/mono number → descriptive text
- Subtle gold glow `rgba(201,168,76,0.08)` behind each stat
- No cards—just spacing and typography hierarchy

---

### **5. Research Demo: "Watch the AI Analyze"**
**Location:** Mid-page engagement  
**Purpose:** Show AI capability live

**Components:**
- Interactive terminal-style demo:
  - Ticker input: "HDFCBANK" (mono font)
  - Button: "Analyze" (gold bg)
  - Shows pulsing dots during thinking: "Scanning documents... 3.2s"
  - AI response appears line-by-line:
    ```
    Score: 74/100
    Moat: Strong (dominant market share)
    Valuation: Fair (10.2x EV/EBITDA)
    Risks: Regulatory headwinds
    Sources: [SEC](link) [BSE](link) [ET](link)
    ```

**Design:**
- `font-family: JetBrains Mono` throughout
- `bg-erebus-depth` with `border: 1px rgba(201,168,76,0.15)` (gold border)
- Text appears with typewriter effect
- Sources appear as blue links
- Pulsing dots animation during thinking

---

### **6. Comparison Table: "vs. Bloomberg / Manual Research"**
**Location:** Conversion consideration  
**Purpose:** Competitive positioning

**Design:**
- Three-column table:
  - Column 1: Feature dimension
  - Column 2: "Bloomberg Terminal" (gray text)
  - Column 3: "EREBUS" (gold checkmark, green text)

**Rows:**
- Cost per year
- India-focused data
- AI-assisted insights
- Real-time scoring
- Source citations
- Mobile-friendly

**Animation:**
- Rows fade in on scroll
- Green checkmarks animate with bounce

---

### **7. Testimonials: "What Analysts Say"**
**Location:** Social proof  
**Purpose:** Build confidence

**Components:**
- Scrolling quote carousel (vertical or horizontal):
  - Quote in serif italic
  - Name + title + company (mono for company ticker)
  - Star rating or credibility marker

**Example Testimonials:**
> "Finally, I can justify saying 'no' to Bloomberg."  
> — Rahul Sharma, Senior Analyst, Motilal Oswal

> "Three minutes from ticker to decision. That's EREBUS."  
> — Priya Venkat, Portfolio Manager, Shareinvest

> "The source citations alone are worth it."  
> — Arjun Nair, Equity Research, SBI Securities

**Design:**
- `bg-erebus-surface` cards
- Gold left border: `border-l: 3px solid #C9A84C`
- No right shadow—glass effect only
- Staggered reveal on scroll

---

### **8. Pricing Section: "Transparent Tiers"**
**Location:** Pre-CTA conversion  
**Purpose:** Show value proposition

**Components:**
- 3 tiers:
  1. **Scout** — ₹0/month (core features)
  2. **Analyst** — ₹2,999/month (AI + source engine)
  3. **Quant** — ₹9,999/month (API access + alerts)

**Design:**
- Tier cards: slightly lifted (shadow or gold glow behind highlight tier)
- Highlight "Analyst" tier with gold accent border
- Feature list per tier (checkmarks in green)
- CTA: "Start 30-day trial" (gold)

---

### **9. FAQ Accordion: "Common Questions"**
**Location:** Trust-building, before final CTA  
**Purpose:** Remove objections

**Sample Questions:**
- "Do you really have India-focused data?"
- "How accurate is the AI scoring?"
- "Can I use EREBUS with my broker's API?"
- "Is my research private?"

**Design:**
- Off-white (erebus-cream) question text
- Gold disclosure arrow (chevron) on right
- Answer text appears with fade-in
- `border-b: 1px rgba(255,255,255,0.07)`

---

### **10. Final CTA: "Start Your Free Trial"**
**Location:** Footer hero  
**Purpose:** Last conversion push

**Components:**
- Headline: "Your Research. Amplified." (serif, italic)
- Subheadline: "30-day free trial. No credit card required."
- CTA button: "Begin analysis" (gold bg, cream text, hover: gold-light)
- Trust line: "Used by 2,000+ analysts across India"

**Animation:**
- Headline animated word-by-word reveal
- Button grows slightly on hover
- Background subtle animation (grid lines or particle field)

---

### **11. Footer**
**Components:**
- Logo + brand statement (one line)
- Four link columns:
  - Product (Docs, Roadmap, API)
  - Company (About, Blog, Careers)
  - Legal (Privacy, Terms, Security)
  - Social (Twitter/X, LinkedIn)
- Copyright line in muted text

**Design:**
- `bg-erebus-void`
- Top border: `border-t: 1px rgba(201,168,76,0.2)` (subtle gold)
- Link text in erebus-secondary, hover: erebus-gold

---

## 📦 Component Architecture

### Directory Structure
```
src/
├── components/
│   ├── erebus/
│   │   ├── HeroSection.jsx
│   │   ├── ProblemCards.jsx
│   │   ├── FeatureCarousel.jsx
│   │   ├── CredibilityStats.jsx
│   │   ├── ResearchDemo.jsx
│   │   ├── ComparisonTable.jsx
│   │   ├── TestimonialCarousel.jsx
│   │   ├── PricingTiers.jsx
│   │   ├── FAQAccordion.jsx
│   │   ├── FinalCTA.jsx
│   │   ├── Footer.jsx
│   │   └── ParticleField.jsx (animation)
│   └── ...existing components
├── styles/
│   ├── erebus.css (global theme + animations)
│   └── tailwind.config.js (color extensions)
└── pages/
    └── LandingPage.jsx (composition)
```

---

## 🎬 Animation & Interaction Strategy

### Entrance Animations
- **Staggered letter reveal** on hero (like NeuroFin, but serif)
- **Fade + slide up** on scroll for sections
- **Stagger cards** in grid (Problem section)
- **Scale + fade** for testimonial cards

### Interactive
- **Hover states**: Gold borders grow/brighten, text glows
- **Typewriter effect** on demo analyzer output
- **Pulsing dots** during AI thinking
- **Smooth scroll** to anchor sections
- **Active states** on FAQ items (chevron rotates, text glows gold)

### Background Motion
- **Particle field** in hero (subtle data flow)
- **Grid lines animation** in final CTA section
- **Stationary** overall (unlike NeuroFin's heavy parallax)—terminal feel prioritizes clarity

### Tool Stack
```
Animation:    GSAP + ScrollTrigger (for scroll-sync)
Transitions:  Tailwind's built-in + custom CSS
Particles:    Custom canvas component (lightweight)
Carousel:     Swiper.js or react-slick (scrollable scenes)
```

---

## 🎨 CSS & Tailwind Strategy

### Custom Global Styles
```css
@font-face {
  font-family: 'DM Serif Display';
  src: url('/fonts/dm-serif-display.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;
}

@font-face {
  font-family: 'DM Serif Display';
  src: url('/fonts/dm-serif-display-italic.woff2') format('woff2');
  font-weight: 400;
  font-style: italic;
}

/* Glassmorphism base */
.glass {
  background: rgba(19, 22, 30, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.07);
  backdrop-filter: blur(10px);
}

/* Gold glow effect */
.gold-glow {
  box-shadow: inset 0 0 30px rgba(201, 168, 76, 0.08);
}

/* Terminal border */
.terminal-border-gold {
  border: 1px solid rgba(201, 168, 76, 0.15);
}

/* Animations */
@keyframes typewriter { /* For demo */ }
@keyframes pulse-dots { /* For AI thinking */ }
@keyframes reveal-word { /* For staggered text */ }
```

### Tailwind Config Extension
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        'erebus-void': '#0D0F14',
        'erebus-surface': '#13161E',
        // ...rest of palette
      },
      fontFamily: {
        'dm-serif': ['DM Serif Display', 'serif'],
        'jetbrains': ['JetBrains Mono', 'monospace'],
      },
      spacing: {
        // Custom for terminal-like gutters
      },
    },
  },
};
```

---

## 📋 Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Tailwind config extended with color palette
- [ ] Import fonts (DM Serif Display, JetBrains Mono)
- [ ] Create `erebus.css` with reusable classes
- [ ] Build `ParticleField.jsx` component
- [ ] Set up GSAP + ScrollTrigger

### Phase 2: Components (Week 2)
- [ ] `HeroSection.jsx` — with particle field
- [ ] `ProblemCards.jsx` — three-card grid
- [ ] `FeatureCarousel.jsx` — horizontal scroll
- [ ] `CredibilityStats.jsx` — three stat blocks
- [ ] `ResearchDemo.jsx` — interactive analyzer

### Phase 3: Mid-Page (Week 3)
- [ ] `ComparisonTable.jsx` — 3-column table
- [ ] `TestimonialCarousel.jsx` — scrolling quotes
- [ ] `PricingTiers.jsx` — subscription cards
- [ ] `FAQAccordion.jsx` — expandable Q&A

### Phase 4: Closing & Polish (Week 4)
- [ ] `FinalCTA.jsx` — conversion hero
- [ ] `Footer.jsx` — navigation footer
- [ ] `LandingPage.jsx` — composition + scroll sync
- [ ] Mobile responsiveness
- [ ] Performance optimization
- [ ] Cross-browser testing

---

## 🚀 Key Differentiators from NeuroFin

| Aspect | NeuroFin | EREBUS |
|--------|----------|--------|
| **Vibe** | Playful, consumer | Serious, institutional |
| **Animations** | Heavy parallax, kinetic | Purposeful, data-focused |
| **Typography** | Syne (modern) | DM Serif (authority) + Mono (terminal) |
| **Color** | Blues, purples | Gold + dark void |
| **Data Presentation** | Narrative-driven | Numbers + sources cited |
| **Copy Tone** | Friendly, Hindi-first | Professional, English-first |
| **Pace** | Fast, playful scroll | Measured, authoritative reveal |

---

## 📱 Responsive Strategy

- **Mobile (< 768px):** Stack all components vertically, single-column layout
- **Tablet (768-1024px):** Two-column sections, mobile carousel for features
- **Desktop (> 1024px):** Full horizontal scroll on features, multi-column tables

---

## ✅ Quality Standards

- **Accessibility:** Semantic HTML, ARIA labels, keyboard nav on carousels
- **Performance:** Lazy-load images, optimize particles (canvas vs DOM)
- **SEO:** Meta tags, structured data for pricing/FAQ, heading hierarchy
- **Brand Consistency:** Every interaction reflects gold/institutional aesthetic

---

End of Implementation Plan.
