// components/erebus/HeroSection.jsx — Sample Hero Component
// This demonstrates the EREBUS design language and animation approach

import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import ScrollTrigger from 'gsap/ScrollTrigger';
import ParticleField from './ParticleField';
import './erebus.css';

gsap.registerPlugin(ScrollTrigger);

export default function HeroSection() {
  const heroRef = useRef(null);
  const titleRef = useRef(null);
  const subtitleRef = useRef(null);
  const ctaRef = useRef(null);

  const HEADLINE = 'Bloomberg Terminal for India';
  const SUBHEADLINE = 'Institutional-grade equity research, without the 24K price tag.';

  useEffect(() => {
    const ctx = gsap.context(() => {
      if (!titleRef.current || !subtitleRef.current) return;

      // Split headline into characters for staggered reveal
      const titleChars = titleRef.current.querySelectorAll('.erebus-char');
      const subtitleLines = subtitleRef.current.querySelectorAll('.erebus-line');
      const ctaButtons = ctaRef.current?.querySelectorAll('button');

      // Reset
      gsap.set(titleChars, { opacity: 0, y: '110%', rotateX: -70 });
      gsap.set(subtitleLines, { opacity: 0, y: 20 });
      gsap.set(ctaButtons, { opacity: 0, y: 30 });

      // Cinematic entrance timeline
      const tl = gsap.timeline({ delay: 0.2 });

      // Headline stagger
      tl.to(titleChars, {
        opacity: 1,
        y: '0%',
        rotateX: 0,
        stagger: 0.05,
        duration: 0.95,
        ease: 'expo.out',
      });

      // Subtitle fade
      tl.to(
        subtitleLines,
        {
          opacity: 1,
          y: 0,
          stagger: 0.08,
          duration: 0.8,
          ease: 'power3.out',
        },
        '-=0.6'
      );

      // CTAs appear
      tl.to(
        ctaButtons,
        {
          opacity: 1,
          y: 0,
          stagger: 0.1,
          duration: 0.7,
          ease: 'power2.out',
        },
        '-=0.5'
      );

      // Scroll parallax on title (scroll down = fade out + translate up)
      ScrollTrigger.create({
        trigger: heroRef.current,
        start: 'top top',
        end: 'bottom top',
        scrub: true,
        onUpdate(self) {
          if (!titleRef.current) return;
          titleRef.current.style.transform = `translateY(${self.progress * 60}px)`;
          titleRef.current.style.opacity = String(1 - self.progress * 1.5);
        },
      });

      // Chevron bounce (scroll indicator)
      const chevron = heroRef.current?.querySelector('.erebus-chevron');
      if (chevron) {
        gsap.to(chevron, {
          y: 12,
          opacity: 0.4,
          duration: 0.8,
          repeat: -1,
          yoyo: true,
          ease: 'sine.inOut',
          delay: 2,
        });
      }
    }, heroRef);

    return () => ctx.revert();
  }, []);

  // Helper to split text into characters
  const splitChars = (text) => {
    return text.split('').map((char, i) => (
      <span key={i} className="erebus-char inline-block">
        {char}
      </span>
    ));
  };

  return (
    <section
      ref={heroRef}
      className="erebus-section relative w-full min-h-screen flex flex-col items-center justify-center overflow-hidden"
      style={{ background: '#0D0F14' }}
    >
      {/* Particle field animation (live data concept) */}
      <div className="absolute inset-0 pointer-events-none opacity-40">
        <ParticleField count={32} color="#C9A84C" speed={0.12} />
      </div>

      {/* Background atmospheric image (optional) */}
      <div className="absolute inset-0 overflow-hidden" style={{ zIndex: 0 }}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(ellipse at 50% 50%, rgba(201,168,76,0.04) 0%, transparent 70%)',
          }}
        />
      </div>

      {/* Content Layer */}
      <div
        className="relative z-10 text-center px-6 max-w-5xl"
        style={{ willChange: 'transform' }}
      >
        {/* Headline */}
        <h1
          ref={titleRef}
          className="font-dm-serif text-5xl md:text-6xl lg:text-7xl font-bold mb-6"
          style={{
            color: '#F0EDE6',
            fontStyle: 'italic',
            letterSpacing: '-0.02em',
            lineHeight: 1.1,
          }}
        >
          {splitChars(HEADLINE)}
        </h1>

        {/* Subheadline */}
        <div
          ref={subtitleRef}
          className="mb-10"
          style={{ color: '#8B8E99' }}
        >
          <p className="erebus-line font-inter text-lg md:text-xl max-w-3xl mx-auto leading-relaxed">
            {SUBHEADLINE}
          </p>
        </div>

        {/* CTAs */}
        <div
          ref={ctaRef}
          className="flex flex-col sm:flex-row gap-4 justify-center items-center"
        >
          {/* Primary CTA: Gold background */}
          <button
            className="px-8 py-3 font-inter font-medium rounded-lg transition-all duration-300"
            style={{
              background: '#C9A84C',
              color: '#0D0F14',
              opacity: 0,
              border: 'none',
              cursor: 'pointer',
              boxShadow: '0 8px 24px rgba(201, 168, 76, 0.2)',
            }}
            onMouseEnter={(e) => {
              gsap.to(e.currentTarget, {
                background: '#D4B560',
                boxShadow: '0 12px 36px rgba(201, 168, 76, 0.35)',
                duration: 0.3,
              });
            }}
            onMouseLeave={(e) => {
              gsap.to(e.currentTarget, {
                background: '#C9A84C',
                boxShadow: '0 8px 24px rgba(201, 168, 76, 0.2)',
                duration: 0.3,
              });
            }}
          >
            Start Free Trial
          </button>

          {/* Secondary CTA: Gold outline */}
          <button
            className="px-8 py-3 font-inter font-medium rounded-lg transition-all duration-300"
            style={{
              background: 'transparent',
              color: '#C9A84C',
              border: '1px solid rgba(201, 168, 76, 0.4)',
              opacity: 0,
              cursor: 'pointer',
            }}
            onMouseEnter={(e) => {
              gsap.to(e.currentTarget, {
                borderColor: 'rgba(201, 168, 76, 1)',
                background: 'rgba(201, 168, 76, 0.05)',
                boxShadow: 'inset 0 0 24px rgba(201, 168, 76, 0.1)',
                duration: 0.3,
              });
            }}
            onMouseLeave={(e) => {
              gsap.to(e.currentTarget, {
                borderColor: 'rgba(201, 168, 76, 0.4)',
                background: 'transparent',
                boxShadow: 'none',
                duration: 0.3,
              });
            }}
          >
            See Feature Tour
          </button>
        </div>
      </div>

      {/* Scroll Indicator */}
      <div
        className="absolute bottom-12 left-1/2 transform -translate-x-1/2 text-erebus-gold"
        style={{ zIndex: 5 }}
      >
        <svg
          className="erebus-chevron w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 14l-7 7m0 0l-7-7m7 7V3"
          />
        </svg>
      </div>
    </section>
  );
}
