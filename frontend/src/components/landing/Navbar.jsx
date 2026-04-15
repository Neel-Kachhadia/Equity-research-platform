import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'

const NAV = [
  { label: 'Features',     href: '#features'    },
  { label: 'Compare',      href: '#compare'     },
  { label: 'Testimonials', href: '#testimonials' },
  { label: 'Pricing',      href: '#pricing'      },
]

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [open,     setOpen]     = useState(false)

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
      style={{
        background: scrolled ? 'rgba(8,10,15,0.92)' : 'transparent',
        backdropFilter: scrolled ? 'blur(14px)' : 'none',
        borderBottom: scrolled ? '1px solid rgba(255,255,255,0.07)' : '1px solid transparent',
      }}
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">

        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 shrink-0">
          <div
            className="w-7 h-7 rounded-full flex items-center justify-center border font-dm-serif text-[13px]"
            style={{ borderColor: 'rgba(201,168,76,0.5)', background: 'rgba(201,168,76,0.1)', color: '#C9A84C' }}
          >
            E
          </div>
          <span className="font-dm-serif text-[18px] tracking-tight text-erebus-text-1">
            EREBUS
          </span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-8">
          {NAV.map(item => (
            <a
              key={item.label}
              href={item.href}
              className="text-[13px] transition-colors"
              style={{ color: '#8A8D9A' }}
              onMouseEnter={e => e.target.style.color = '#EEE9E0'}
              onMouseLeave={e => e.target.style.color = '#8A8D9A'}
            >
              {item.label}
            </a>
          ))}
        </div>

        {/* Right CTAs */}
        <div className="hidden md:flex items-center gap-3">
          <Link
            to="/login"
            className="text-[13px] transition-colors"
            style={{ color: '#8A8D9A' }}
            onMouseEnter={e => e.target.style.color = '#C9A84C'}
            onMouseLeave={e => e.target.style.color = '#8A8D9A'}
          >
            Sign in
          </Link>
          <Link
            to="/signup"
            className="px-5 py-2 rounded-lg text-[13px] font-medium btn-gold"
          >
            Start free →
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden flex flex-col gap-1.5 p-2"
          onClick={() => setOpen(o => !o)}
          aria-label="Toggle menu"
        >
          {[0,1,2].map(i => (
            <span
              key={i}
              className="block w-5 h-0.5 rounded-full transition-all duration-300"
              style={{ background: '#C9A84C' }}
            />
          ))}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div
          className="md:hidden px-6 pb-6 space-y-4 animate-fade-in"
          style={{ background: 'rgba(8,10,15,0.97)', borderTop: '1px solid rgba(255,255,255,0.07)' }}
        >
          {NAV.map(item => (
            <a
              key={item.label}
              href={item.href}
              onClick={() => setOpen(false)}
              className="block text-[15px] py-2"
              style={{ color: '#8A8D9A' }}
            >
              {item.label}
            </a>
          ))}
          <div className="flex gap-3 pt-2">
            <Link to="/login"  className="flex-1 text-center py-2.5 rounded-lg cta-button-secondary text-[14px]">Sign in</Link>
            <Link to="/signup" className="flex-1 text-center py-2.5 rounded-lg cta-button-primary  text-[14px]">Start free</Link>
          </div>
        </div>
      )}
    </nav>
  )
}
