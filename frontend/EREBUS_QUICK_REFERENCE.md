# EREBUS Landing Page — Quick Reference & Handoff Guide
**For: Antigravity Development Team**

---

## 📦 What You're Getting

Four files have been prepared to help you transform the existing landing page into EREBUS:

1. **EREBUS_LANDING_IMPLEMENTATION_PLAN.md** — Complete specification & component breakdown
2. **EREBUS_TAILWIND_CONFIG.js** — Color palette & typography configuration
3. **EREBUS_GLOBAL_STYLES.css** — Reusable classes, animations & utilities
4. **EREBUS_HERO_COMPONENT_EXAMPLE.jsx** — Sample component showing the design language
5. **EREBUS_QUICK_REFERENCE.md** (this file) — Dev team quick reference

---

## 🎨 The EREBUS Aesthetic in 60 Seconds

**Vibe:** Bloomberg Terminal meets AI precision  
**Color:** Dark void (#0D0F14) + gold authority (#C9A84C)  
**Typography:** DM Serif Display (headlines) + Inter (body) + JetBrains Mono (data)  
**Feel:** Institutional, serious, data-rich, no flourish

---

## 🚀 Quick Setup

### 1. Update `tailwind.config.js`
Copy the contents of `EREBUS_TAILWIND_CONFIG.js` into the `extend` section of your existing Tailwind config. This adds:
- EREBUS color palette (`erebus-void`, `erebus-gold`, etc.)
- Custom fonts
- Terminal-scale typography
- Animation keyframes

### 2. Import Global Styles
In your main CSS/global styles file, add:
```jsx
import './erebus.css'; // Make sure EREBUS_GLOBAL_STYLES.css is renamed and imported
```

### 3. Import Google Fonts
Add this to your HTML `<head>` or CSS:
```html
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
```

---

## 🧩 Component Structure

### Hero Section
```jsx
<HeroSection />
// From: EREBUS_HERO_COMPONENT_EXAMPLE.jsx
// Shows: Animated headline + subtitle + 2 CTAs + particle field
// Key Classes: erebus-section, erebus-char, cta-button-primary, cta-button-secondary
```

### Problem Cards (3 constraint grid)
```jsx
<div className="erebus-3-column my-8">
  <div className="erebus-card gold-top-border">
    <div className="erebus-label">COST</div>
    <h3>₹2L/year vs ₹0-5L</h3>
    <p className="text-erebus-secondary">Bloomberg pricing vs EREBUS</p>
  </div>
  {/* ... repeat for other cards */}
</div>
```

### Feature Carousel
```jsx
<div className="erebus-carousel">
  {SCENES.map(scene => (
    <div key={scene.id} className="erebus-scene flex-shrink-0 w-full">
      <div className="erebus-label">{scene.number}</div>
      <h3 className="font-dm-serif">{scene.title}</h3>
      <img src={scene.img} alt="" />
    </div>
  ))}
</div>
```

### Stat Block
```jsx
<div className="text-center">
  <div className="mono-score">{stat.value}</div>
  <div className="erebus-label mt-2">{stat.label}</div>
  <p className="text-erebus-secondary">{stat.description}</p>
</div>
```

### Interactive Demo
```jsx
<div className="gold-border glass px-6 py-8">
  <input className="bg-erebus-depth border-erebus-border text-erebus-cream" 
         placeholder="Enter ticker..." />
  <button className="cta-button-primary">Analyze</button>
  
  {/* Thinking state */}
  <div>Scanning documents
    <span className="erebus-pulse-dot"></span>
    <span className="erebus-pulse-dot"></span>
    <span className="erebus-pulse-dot"></span>
  </div>
  
  {/* Response appears line by line */}
</div>
```

### Testimonial Card
```jsx
<div className="erebus-card gold-left-border">
  <p className="font-dm-serif italic">"{quote}"</p>
  <div className="mt-4 text-erebus-secondary">
    <div className="font-medium">{name}</div>
    <div className="mono">{title} · {company}</div>
  </div>
</div>
```

### Pricing Card (Featured)
```jsx
<div className="erebus-card-featured mb-4">
  <div className="erebus-label">₹2,999/MONTH</div>
  <h3>Analyst</h3>
  <ul>
    <li className="text-erebus-positive">✓ AI scoring engine</li>
    {/* ... more features */}
  </ul>
  <button className="cta-button-primary w-full mt-4">Start Trial</button>
</div>
```

---

## 🎭 Animation Patterns

### Staggered Character Reveal (Hero)
```javascript
const chars = heroRef.current.querySelectorAll('.erebus-char');
gsap.set(chars, { opacity: 0, y: '110%', rotateX: -70 });
gsap.to(chars, {
  opacity: 1, y: '0%', rotateX: 0,
  stagger: 0.05, duration: 0.95, ease: 'expo.out'
});
```

### Fade + Slide Up (Section Entrance)
```javascript
gsap.from(sectionRef.current.querySelectorAll('.erebus-card'), {
  opacity: 0, y: 30,
  stagger: 0.1, duration: 0.8, ease: 'power3.out',
  scrollTrigger: { trigger: sectionRef.current, start: 'top 75%', once: true }
});
```

### Gold Glow on Hover
```javascript
element.addEventListener('mouseenter', () => {
  gsap.to(element, {
    boxShadow: 'inset 0 0 30px rgba(201, 168, 76, 0.12)',
    borderColor: 'rgba(201, 168, 76, 0.3)',
    duration: 0.3
  });
});
```

### Pulsing Dots (AI Thinking)
The CSS class `erebus-pulse-dot` handles this:
```jsx
<span className="erebus-pulse-dot"></span>
<span className="erebus-pulse-dot"></span>
<span className="erebus-pulse-dot"></span>
```

---

## 📐 Spacing & Sizing Conventions

| Element | Tailwind | Purpose |
|---------|----------|---------|
| Section padding | `py-16 md:py-24 lg:py-32` | Breathing room between sections |
| Component gap | `gap-6 md:gap-8` | Space between cards/items |
| Card padding | `p-6 md:p-8` | Interior card spacing |
| Border radius | `rounded-lg` (8px) | Subtle, not rounded |
| Font size | Handled by CSS vars | Use `clamp()` for fluid scaling |

---

## 🎨 Reusable CSS Classes

### Backgrounds
- **`.erebus-void`** → `#0D0F14` (primary bg)
- **`.erebus-surface`** → `#13161E` (lifted panels)
- **`.erebus-depth`** → `#1A1D26` (deepest)

### Status/Semantic
- **`.erebus-positive`** → Green (#3ECF8E)
- **`.erebus-negative`** → Red (#E55C5C)
- **`.erebus-warning`** → Amber (#F0A429)
- **`.erebus-link`** → Blue (#4A8FE7)

### Components
- **`.erebus-card`** → Glass card with hover state
- **`.erebus-card-featured`** → Highlighted tier pricing
- **`.glass`** → Base glassmorphism
- **`.gold-glow`** → Inset gold illumination
- **`.erebus-carousel`** → Scrollable flex container

### Buttons
- **`.cta-button-primary`** → Gold solid fill
- **`.cta-button-secondary`** → Gold outline

### Text
- **`.erebus-label`** → Mono uppercase labels
- **`.mono-score`** → Large data numbers
- **`.erebus-accent`** → Gold colored text

---

## ✅ Checklist Before Handing Off

- [ ] Tailwind config extended with EREBUS colors
- [ ] Google Fonts imported (DM Serif Display, Inter, JetBrains Mono)
- [ ] EREBUS global styles imported
- [ ] Hero component implemented with animations
- [ ] Problem cards section built
- [ ] Feature carousel with horizontal scroll
- [ ] Credibility stats with gold glows
- [ ] AI demo with typewriter + pulsing dots
- [ ] Testimonials carousel
- [ ] Pricing tiers (highlight Analyst plan)
- [ ] FAQ accordion
- [ ] Final CTA section
- [ ] Footer with gold accent border
- [ ] Mobile responsive (test on <640px, 640-1024px, >1024px)
- [ ] Cross-browser testing (Chrome, Firefox, Safari, Edge)
- [ ] Performance check (Lighthouse)
- [ ] Accessibility audit (WCAG 2.1)

---

## 📱 Responsive Breakpoints

- **Mobile (< 640px):** Single column, large padding, stack cards vertically
- **Tablet (640 - 1024px):** Two columns, medium padding
- **Desktop (> 1024px):** Three columns, full padding, horizontal scrolls enabled

---

## 🔗 Key Dependencies

```json
{
  "react": "^18.0.0",
  "gsap": "^3.12.0+",
  "tailwindcss": "^3.3.0+",
  "swiper": "^11.0.0" // Optional, for advanced carousel
}
```

---

## 💡 Design Philosophy Reminders

1. **Gold is authority** — Every CTA, active state, logo should use #C9A84C
2. **Minimal, not sparse** — Dense information but never cluttered
3. **Institutional tone** — No emojis, no playfulness in data sections
4. **Precision animations** — Purpose-driven, not decorative
5. **Source citations** — Every claim links back (blue links #4A8FE7)
6. **Terminal aesthetic** — Monospace for anything "live" or numeric

---

## 🤝 Questions for Clarification

Before starting, confirm with stakeholders:

1. **Copy finalization** — Do you have finalized messaging, or should we use placeholders?
2. **Image assets** — Do you have dashboard screenshots, researcher photos for testimonials?
3. **Video** — Does the final CTA section need a video background?
4. **Social proof** — How many analysts/testimonials do you have for the carousel?
5. **Analytics** — Which tracking events are critical (CTA clicks, scroll depth)?

---

## 📊 Performance Targets

- **Lighthouse Score:** 85+ (Performance, Accessibility, Best Practices, SEO)
- **First Contentful Paint:** < 2s
- **Largest Contentful Paint:** < 2.5s
- **Cumulative Layout Shift:** < 0.1

---

End of Quick Reference.  
Good luck with EREBUS! 🚀
