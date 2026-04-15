// src/components/landing/ClosingCTA.jsx
import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'

export default function ClosingCTA() {
  return (
    <section className="py-32 px-8 lg:px-20 bg-erebus-bg relative overflow-hidden">

      {/* Radial glow backdrop */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse 70% 60% at 50% 50%, rgba(201,168,76,0.05) 0%, transparent 70%)',
        }}
      />

      {/* Fine horizontal lines for depth */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.025]"
        style={{
          backgroundImage: 'repeating-linear-gradient(0deg, rgba(255,255,255,0.5) 0px, rgba(255,255,255,0.5) 1px, transparent 1px, transparent 80px)',
        }}
      />

      <div className="max-w-3xl mx-auto text-center relative z-10">
        <div className="section-label mb-8">Get Started</div>

        <h2 className="font-serif text-[52px] md:text-[64px] text-erebus-text-1 leading-[1.05] mb-6">
          Stop guessing.<br />
          <span className="text-gradient-gold italic">Start researching.</span>
        </h2>

        <p className="text-[17px] text-erebus-text-2 leading-relaxed max-w-lg mx-auto mb-12">
          Join over 1,200 analysts already using EREBUS to research Indian equities with institutional precision — at a fraction of the cost.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            to="/signup"
            className="flex items-center justify-center gap-2 px-8 py-4 rounded-md text-[15px] font-semibold btn-gold"
          >
            Start for free
            <ArrowRight size={16} />
          </Link>
          <Link
            to="/login"
            className="flex items-center justify-center gap-2 px-8 py-4 rounded-md text-[15px] btn-ghost"
          >
            Sign in to workspace
          </Link>
        </div>

        <p className="mt-8 text-[12px] font-mono text-erebus-text-3">
          No credit card required · SEBI-compliant · 14-day Pro trial
        </p>
      </div>
    </section>
  )
}
