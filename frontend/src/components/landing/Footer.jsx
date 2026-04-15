import { Link } from 'react-router-dom'

const LINKS = [
  {
    heading: 'Product',
    items: [
      { label: 'Research Chat',  to: '/app' },
      { label: 'Scorecard',      to: '/app/scorecard' },
      { label: 'Compare',        to: '/app/compare' },
      { label: 'API Docs',       to: '#' },
    ],
  },
  {
    heading: 'Company',
    items: [
      { label: 'About',    to: '#' },
      { label: 'Blog',     to: '#' },
      { label: 'Careers',  to: '#' },
      { label: 'Contact',  to: '#' },
    ],
  },
  {
    heading: 'Legal',
    items: [
      { label: 'Privacy Policy', to: '#' },
      { label: 'Terms of Use',   to: '#' },
      { label: 'Security',       to: '#' },
      { label: 'SEBI Disclaimer',to: '#' },
    ],
  },
  {
    heading: 'Connect',
    items: [
      { label: 'Twitter / X',  to: '#' },
      { label: 'LinkedIn',     to: '#' },
      { label: 'GitHub',       to: '#' },
      { label: 'Discord',      to: '#' },
    ],
  },
]

export default function Footer() {
  return (
    <footer
      className="bg-erebus-bg"
      style={{ borderTop: '1px solid rgba(201,168,76,0.18)' }}
    >
      <div className="max-w-6xl mx-auto px-8 py-14">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">

          {/* Brand column */}
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center border
                           font-dm-serif text-erebus-gold text-[13px]"
                style={{ borderColor: 'rgba(201,168,76,0.4)', background: 'rgba(201,168,76,0.08)' }}
              >
                E
              </div>
              <span className="font-dm-serif text-[18px] text-erebus-gold tracking-tight">
                EREBUS
              </span>
            </div>
            <p className="text-[13px] leading-[1.7]" style={{ color: '#4E5262' }}>
              Institutional-grade equity research intelligence for India.
            </p>
          </div>

          {/* Link columns */}
          {LINKS.map(col => (
            <div key={col.heading}>
              <p className="erebus-label mb-4">{col.heading}</p>
              <ul className="space-y-3">
                {col.items.map(item => (
                  <li key={item.label}>
                    <Link
                      to={item.to}
                      className="text-[13px] transition-colors"
                      style={{ color: '#8A8D9A' }}
                      onMouseEnter={e => e.target.style.color = '#C9A84C'}
                      onMouseLeave={e => e.target.style.color = '#8A8D9A'}
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div
          className="flex flex-col md:flex-row items-center justify-between gap-3 pt-6"
          style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}
        >
          <p className="font-jetbrains text-[11px] tracking-[0.05em]" style={{ color: '#4E5262' }}>
            © 2024 EREBUS · All rights reserved
          </p>
          <p className="font-jetbrains text-[11px]" style={{ color: '#4E5262', textAlign: 'center' }}>
            Not investment advice · For informational use only · All data sourced from public SEBI/NSE/BSE filings
          </p>
        </div>
      </div>
    </footer>
  )
}
