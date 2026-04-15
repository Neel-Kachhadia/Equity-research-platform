// tailwind.config.js — EREBUS Color System Extension
module.exports = {
  theme: {
    extend: {
      colors: {
        // ── EREBUS Brand Palette ──
        erebus: {
          'void': '#0D0F14',        // Primary background
          'surface': '#13161E',     // Panels & lifted elements
          'depth': '#1A1D26',       // Deepest surfaces
          'cream': '#F0EDE6',       // Primary text
          'secondary': '#8B8E99',   // Secondary info
          'muted': '#545769',       // Timestamps, muted
          'gold': '#C9A84C',        // Brand accent (CTAs, active)
          'gold-light': '#D4B560',  // Hover states
          'green': '#3ECF8E',       // Gains, positive
          'red': '#E55C5C',         // Losses, risk
          'amber': '#F0A429',       // Warnings, guidance misses
          'blue': '#4A8FE7',        // Sources, links
        },
      },
      fontFamily: {
        'dm-serif': ['DM Serif Display', 'serif'],
        'jetbrains': ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        // Terminal-scale macro typography
        'terminal-sm': ['0.65rem', { lineHeight: '1.2', letterSpacing: '0.05em' }],
        'terminal-md': ['0.85rem', { lineHeight: '1.4', letterSpacing: '0.03em' }],
        'headline': ['clamp(2.5rem, 8vw, 5rem)', { lineHeight: '1.1', fontWeight: 'bold' }],
      },
      spacing: {
        'section': 'clamp(2rem, 4vw, 8rem)',
      },
      borderWidth: {
        'gold-top': '2px',
      },
      boxShadow: {
        'erebus-glow': 'inset 0 0 30px rgba(201, 168, 76, 0.08)',
        'erebus-border': '0 0 1px rgba(201, 168, 76, 0.15)',
      },
      backdropFilter: {
        'glass': 'blur(10px)',
      },
      keyframes: {
        'typewriter': {
          '0%': { maxWidth: '0' },
          '100%': { maxWidth: '100%' },
        },
        'pulse-dot': {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '1' },
        },
        'reveal-word': {
          '0%': { opacity: '0', y: '110%' },
          '100%': { opacity: '1', y: '0' },
        },
        'gold-border-grow': {
          '0%': { width: '0' },
          '100%': { width: '100%' },
        },
      },
      animation: {
        'typewriter': 'typewriter 0.1s linear forwards',
        'pulse-dot': 'pulse-dot 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'reveal-word': 'reveal-word 1s ease-out forwards',
        'gold-border-grow': 'gold-border-grow 0.6s ease-out forwards',
      },
    },
  },
};
