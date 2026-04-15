// GlobalBackground.jsx — Fixed animated orb layer behind all sections
// Uses CSS radial-gradient blobs + keyframe drift animations (no canvas, low perf impact)
export default function GlobalBackground() {
  return (
    <div
      style={{
        position: 'fixed', inset: 0,
        pointerEvents: 'none',
        zIndex: 0,
        overflow: 'hidden',
      }}
    >
      {/* ── Dot grid ─────────────────────────────────────────── */}
      <div
        style={{
          position: 'absolute', inset: 0,
          backgroundImage: 'radial-gradient(rgba(255,255,255,0.055) 1px, transparent 1px)',
          backgroundSize: '36px 36px',
          maskImage: 'linear-gradient(to bottom, black 0%, transparent 100%)',
          WebkitMaskImage: 'linear-gradient(to bottom, black 0%, transparent 100%)',
        }}
      />

      {/* ── Orb 1 — Gold · top-center ────────────────────────── */}
      <div
        style={{
          position: 'absolute',
          width: '900px', height: '900px',
          borderRadius: '50%',
          background: 'radial-gradient(circle at center, rgba(201,168,76,0.18) 0%, transparent 65%)',
          top: '-320px', left: '50%', transform: 'translateX(-50%)',
          animation: 'orb-drift-1 30s ease-in-out infinite',
        }}
      />

      {/* ── Orb 2 — Blue · bottom-right ─────────────────────── */}
      <div
        style={{
          position: 'absolute',
          width: '800px', height: '800px',
          borderRadius: '50%',
          background: 'radial-gradient(circle at center, rgba(74,143,231,0.13) 0%, transparent 65%)',
          bottom: '0%', right: '-180px',
          animation: 'orb-drift-2 38s ease-in-out infinite',
        }}
      />

      {/* ── Orb 3 — Violet · left-mid ────────────────────────── */}
      <div
        style={{
          position: 'absolute',
          width: '700px', height: '700px',
          borderRadius: '50%',
          background: 'radial-gradient(circle at center, rgba(130,80,210,0.10) 0%, transparent 65%)',
          top: '35%', left: '-180px',
          animation: 'orb-drift-3 26s ease-in-out infinite',
        }}
      />

      {/* ── Orb 4 — Teal · bottom-left ───────────────────────── */}
      <div
        style={{
          position: 'absolute',
          width: '600px', height: '600px',
          borderRadius: '50%',
          background: 'radial-gradient(circle at center, rgba(46,204,138,0.09) 0%, transparent 65%)',
          bottom: '15%', left: '5%',
          animation: 'orb-drift-4 32s ease-in-out infinite reverse',
        }}
      />

      {/* ── Orb 5 — Gold · mid-right (subtle) ───────────────── */}
      <div
        style={{
          position: 'absolute',
          width: '500px', height: '500px',
          borderRadius: '50%',
          background: 'radial-gradient(circle at center, rgba(201,168,76,0.08) 0%, transparent 65%)',
          top: '55%', right: '5%',
          animation: 'orb-drift-2 22s ease-in-out infinite reverse',
        }}
      />

      {/* ── Noise grain overlay ───────────────────────────────── */}
      <div
        style={{
          position: 'absolute', inset: 0,
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
          backgroundSize: '256px 256px',
          opacity: 0.35,
        }}
      />
    </div>
  )
}
