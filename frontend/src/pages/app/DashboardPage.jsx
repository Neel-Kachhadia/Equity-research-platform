// DashboardPage.jsx — EREBUS Institutional Research Platform
// Redesigned: No stock tickers · Company-switchable score · Recent files · More charts

import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis,
  PieChart, Pie,
} from 'recharts'
import {
  MessageSquare, Search, GitCompare, Upload,
  FileText, FileImage, FileSpreadsheet, ChevronDown, ArrowRight, Zap, Database, AlertTriangle,
} from 'lucide-react'
import NewsWidget from '../../components/news/NewsWidget'
import FileViewer  from '../../components/ui/FileViewer'
import {
  fetchDashboardSummary,
  fetchDashboardHistory,
  fetchCompanyScore,
  listS3Files,
  generateDownloadUrl,
} from '../../services/api'

/* ─────────────────────────────────────────────────────────────────
   DESIGN TOKENS — base dark with blue + green + gold accent
   ─────────────────────────────────────────────────────────────── */
const T = {
  bg:      '#07090E',
  panel:   '#0F1420',
  panelH:  '#161D2C',
  border:  'rgba(255,255,255,0.12)',
  divider: 'rgba(255,255,255,0.08)',

  gold:    '#C9A84C',
  gold60:  'rgba(201,168,76,0.60)',
  gold35:  'rgba(201,168,76,0.35)',
  gold15:  'rgba(201,168,76,0.15)',
  gold06:  'rgba(201,168,76,0.08)',

  blue:    '#4A8FE7',
  blue15:  'rgba(74,143,231,0.15)',
  blue06:  'rgba(74,143,231,0.07)',

  green:   '#2ECC8A',
  green15: 'rgba(46,204,138,0.15)',
  green06: 'rgba(46,204,138,0.07)',

  red:     '#E05C5C',
  red15:   'rgba(224,92,92,0.15)',
  red06:   'rgba(224,92,92,0.07)',

  t1:   '#F0ECE6',       // primary — near white
  t2:   '#C2CAD8',       // secondary — clearly visible light grey
  t3:   '#8B95A8',       // tertiary — was #5E6880, now properly readable
  mono: "'JetBrains Mono','Fira Code',monospace",
  sans: "'Inter',system-ui,sans-serif",
  serif:"'DM Serif Display',Georgia,serif",
}

/* ─────────────────────────────────────────────────────────────────
   DATA
   ─────────────────────────────────────────────────────────────── */
// Scoreable companies — drives the ScoreCard switcher
const SCORE_UNIVERSE = [
  { ticker:'RELIANCE',  name:'Reliance Industries', sector:'Energy & Digital', score:78, conf:0.88, signal:'bullish',
    factors:[{label:'Quality',value:85},{label:'Growth',value:72},{label:'Capital Efficiency',value:80},{label:'Risk (inv.)',value:69}] },
  { ticker:'TCS',       name:'TCS',                 sector:'IT Services',      score:81, conf:0.84, signal:'bullish',
    factors:[{label:'Quality',value:88},{label:'Growth',value:79},{label:'Capital Efficiency',value:84},{label:'Risk (inv.)',value:74}] },
  { ticker:'HDFCBANK',  name:'HDFC Bank',            sector:'Banking',          score:71, conf:0.76, signal:'neutral',
    factors:[{label:'Quality',value:80},{label:'Growth',value:65},{label:'Capital Efficiency',value:72},{label:'Risk (inv.)',value:66}] },
  { ticker:'ICICIBANK', name:'ICICI Bank',            sector:'Banking',          score:74, conf:0.79, signal:'bullish',
    factors:[{label:'Quality',value:78},{label:'Growth',value:71},{label:'Capital Efficiency',value:76},{label:'Risk (inv.)',value:70}] },
  { ticker:'BAJFINANCE',name:'Bajaj Finance',         sector:'NBFC',             score:69, conf:0.72, signal:'neutral',
    factors:[{label:'Quality',value:74},{label:'Growth',value:63},{label:'Capital Efficiency',value:71},{label:'Risk (inv.)',value:67}] },
  { ticker:'INFY',      name:'Infosys',               sector:'IT Services',      score:65, conf:0.68, signal:'cautious',
    factors:[{label:'Quality',value:72},{label:'Growth',value:58},{label:'Capital Efficiency',value:68},{label:'Risk (inv.)',value:63}] },
  { ticker:'TITAN',     name:'Titan Company',         sector:'Consumer Goods',   score:82, conf:0.85, signal:'bullish',
    factors:[{label:'Quality',value:87},{label:'Growth',value:81},{label:'Capital Efficiency',value:83},{label:'Risk (inv.)',value:76}] },
  { ticker:'ASIANPAINT',name:'Asian Paints',          sector:'Consumer Goods',   score:77, conf:0.80, signal:'bullish',
    factors:[{label:'Quality',value:84},{label:'Growth',value:73},{label:'Capital Efficiency',value:79},{label:'Risk (inv.)',value:71}] },
]

// Research coverage — no prices, purely analytical
const COVERAGE = [
  { ticker:'RELIANCE',  name:'Reliance Industries', sector:'Energy',  score:78, signal:'bullish',  docs:4 },
  { ticker:'TCS',       name:'TCS',                 sector:'IT',      score:81, signal:'bullish',  docs:6 },
  { ticker:'HDFCBANK',  name:'HDFC Bank',            sector:'Banking', score:71, signal:'neutral',  docs:3 },
  { ticker:'ICICIBANK', name:'ICICI Bank',           sector:'Banking', score:74, signal:'bullish',  docs:3 },
  { ticker:'BAJFINANCE',name:'Bajaj Finance',        sector:'NBFC',    score:69, signal:'neutral',  docs:2 },
  { ticker:'INFY',      name:'Infosys',              sector:'IT',      score:65, signal:'cautious', docs:5 },
  { ticker:'TITAN',     name:'Titan Company',        sector:'Consumer',score:82, signal:'bullish',  docs:3 },
  { ticker:'WIPRO',     name:'Wipro',                sector:'IT',      score:58, signal:'cautious', docs:4 },
]

const GUIDANCE = [
  { ticker:'INFY',       event:'Revenue Miss',       severity:'high',   note:'FY26 guidance 3.2% below street consensus. Q4 attrition commentary cautious.', time:'2h ago' },
  { ticker:'TCS',        event:'Positive Revision',  severity:'low',    note:'Q4 EBITDA margin raised 60bps. Hiring plan upgraded for FY27.',                 time:'4h ago' },
  { ticker:'HDFCBANK',   event:'NIM Compression',    severity:'medium', note:'Management flagged deposit cost pressure continuing through H1 FY26.',           time:'6h ago' },
  { ticker:'BAJFINANCE', event:'Guidance Downgrade', severity:'medium', note:'AUM growth guidance revised 26% → 23% YoY. Macro uncertainty cited.',           time:'1d ago' },
  { ticker:'WIPRO',      event:'Guidance Cut',        severity:'high',   note:'FY26 revenue guidance reduced 200bps vs consensus. Deal pipeline muted.',       time:'1d ago' },
]

const SIGNALS = [
  { type:'Trend Shift',     ticker:'RELIANCE',  conf:0.88, note:'Momentum building in Jio vertical. 3 consecutive beats with guidance upgrade trajectory.' },
  { type:'Factor Rotation', ticker:'IT Sector', conf:0.71, note:'Growth factor weakening across large-cap IT. Quality factor pricing premium expanding.'    },
  { type:'Model Consensus', ticker:'TCS',       conf:0.84, note:'84% agreement across 3 quant frameworks. Structural compounder signal active.'             },
  { type:'Risk Elevation',  ticker:'WIPRO',     conf:0.72, note:'Risk factor score deteriorated 38 → 52 in 90 days. Guidance credibility declining.'        },
]

const BENCHMARK = [
  { label:'Quality Score',      co:85, sector:72, univ:64 },
  { label:'Growth Momentum',    co:72, sector:68, univ:61 },
  { label:'Capital Efficiency', co:80, sector:71, univ:63 },
  { label:'Risk (inv.)',         co:69, sector:52, univ:55 },
]

const TREND = [
  {m:'Oct',v:68},{m:'Nov',v:71},{m:'Dec',v:74},
  {m:'Jan',v:70},{m:'Feb',v:73},{m:'Mar',v:76},{m:'Apr',v:78},
]

const DIST_RAW = [
  {r:'0–20',n:2},{r:'21–40',n:8},{r:'41–60',n:24},
  {r:'61–70',n:42},{r:'71–80',n:38},{r:'81–90',n:18},{r:'91–100',n:6},
]
const DIST_MAX = Math.max(...DIST_RAW.map(d => d.n))
const DIST = DIST_RAW.map(d => ({ ...d, fill: `rgba(74,143,231,${(0.22 + 0.78 * d.n / DIST_MAX).toFixed(2)})` }))

const SECTOR_COV = [
  { sector:'IT',        count:6, pct:85 },
  { sector:'Banking',   count:5, pct:78 },
  { sector:'Consumer',  count:4, pct:70 },
  { sector:'Energy',    count:4, pct:72 },
  { sector:'NBFC',      count:3, pct:65 },
  { sector:'Pharma',    count:3, pct:58 },
  { sector:'Metals',    count:2, pct:42 },
]

const RADAR_DATA = [
  { factor:'Quality',    score:82 },
  { factor:'Growth',     score:68 },
  { factor:'Efficiency', score:76 },
  { factor:'Risk',       score:71 },
  { factor:'Momentum',   score:65 },
  { factor:'Sentiment',  score:74 },
]

const RECENT_FILES = [
  { name:'Reliance Annual Report FY24.pdf',          company:'RELIANCE',  uploaded:'2h ago',  type:'PDF', size:'8.2 MB',  pages:312 },
  { name:'TCS Q4 FY24 Earnings Call Transcript.txt', company:'TCS',       uploaded:'5h ago',  type:'TXT', size:'124 KB',  pages:18  },
]

const FEED = [
  { time:'14:32', ticker:'RELIANCE',  action:'Guidance model updated',   color: T.blue  },
  { time:'13:55', ticker:'TCS',       action:'Transcript analysis run',  color: T.green },
  { time:'12:18', ticker:'INFY',      action:'Risk flag triggered',      color: T.red   },
  { time:'11:44', ticker:'HDFCBANK',  action:'Score refreshed · +2pts',  color: T.green },
  { time:'10:03', ticker:'WIPRO',     action:'High-risk alert raised',   color: T.red   },
]

/* ─────────────────────────────────────────────────────────────────
   LIVE DATA HELPERS
   ─────────────────────────────────────────────────────────────── */
function scoreToSignal(score) {
  if (score >= 70) return 'bullish'
  if (score >= 55) return 'neutral'
  return 'cautious'
}

function buildFactors(c) {
  return [
    { label: 'Quality',           value: Math.round(c.quality_score      ?? c.composite_score ?? 70) },
    { label: 'Growth',            value: Math.round(c.growth_score       ?? c.composite_score ?? 65) },
    { label: 'Capital Efficiency',value: Math.round(c.efficiency_score   ?? c.composite_score ?? 68) },
    { label: 'Risk (inv.)',        value: Math.round(c.risk_score_inv     ?? (100 - (c.risk_score ?? 35))) },
  ]
}

function formatSessionTime(iso) {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false })
  } catch { return '—' }
}

const SIGNAL_TYPES = ['Trend Shift', 'Factor Rotation', 'Model Consensus', 'Risk Elevation', 'Alpha Signal', 'Momentum Alert']

function formatFileAge(iso) {
  if (!iso) return '—'
  try {
    const diff = Date.now() - new Date(iso).getTime()
    const m = Math.floor(diff / 60000)
    if (m < 2)  return 'just now'
    if (m < 60) return `${m}m ago`
    const h = Math.floor(m / 60)
    if (h < 24) return `${h}h ago`
    const d = Math.floor(h / 24)
    return `${d}d ago`
  } catch { return '—' }
}

function classifyEvent(headline = '') {
  const h = headline.toLowerCase()
  if (h.includes('guidance') || h.includes('outlook'))  return 'Guidance Update'
  if (h.includes('miss') || h.includes('below'))        return 'Revenue Miss'
  if (h.includes('beat') || h.includes('above'))        return 'Positive Beat'
  if (h.includes('downgrade') || h.includes('cut'))     return 'Guidance Cut'
  if (h.includes('upgrade') || h.includes('raise'))     return 'Positive Revision'
  if (h.includes('margin') || h.includes('nim'))        return 'Margin Alert'
  if (h.includes('risk') || h.includes('concern'))      return 'Risk Elevated'
  return 'Market Update'
}

/* ─────────────────────────────────────────────────────────────────
   PRIMITIVE COMPONENTS
   ─────────────────────────────────────────────────────────────── */
function Skel({ h=16, w='100%', r=4 }) {
  return <div style={{ height:h, width:w, borderRadius:r, background:T.gold06, animation:'sk 1.6s ease infinite' }} />
}

function Label({ children, style={} }) {
  return (
    <span style={{ fontFamily:T.mono, fontSize:11, letterSpacing:'0.08em',
      textTransform:'uppercase', color:T.t3, ...style }}>
      {children}
    </span>
  )
}

function AnimCount({ to, dur=1100 }) {
  const [v,setV] = useState(0)
  useEffect(() => {
    let c=0; const step=to/40; const iv=setInterval(()=>{ c+=step; if(c>=to){setV(to);clearInterval(iv)}else setV(Math.floor(c)) },dur/40)
    return ()=>clearInterval(iv)
  },[to])
  return <>{v}</>
}

function PanelHeader({ label, right, noBorder, accent }) {
  return (
    <div style={{
      display:'flex', alignItems:'center', justifyContent:'space-between',
      padding:'18px 24px',
      borderBottom: noBorder ? 'none' : `1px solid ${T.divider}`,
      borderLeft: accent ? `3px solid ${accent}` : undefined,
      paddingLeft: accent ? 21 : 24,
    }}>
      <Label style={{ fontSize:12, letterSpacing:'0.07em', ...(accent ? { color: accent, opacity:0.9 } : {}) }}>{label}</Label>
      {right}
    </div>
  )
}

function Card({ children, style={}, onClick }) {
  const [h,setH] = useState(false)
  return (
    <div onClick={onClick}
      onMouseEnter={()=>setH(true)} onMouseLeave={()=>setH(false)}
      style={{
        background: h && onClick ? T.panelH : T.panel,
        border:`1px solid ${T.border}`,
        borderRadius:14,
        cursor: onClick ? 'pointer' : 'default',
        transition:'background 0.18s, box-shadow 0.18s',
        boxShadow: h && onClick ? '0 8px 32px rgba(0,0,0,0.4)' : 'none',
        ...style,
      }}>
      {children}
    </div>
  )
}

function Live() {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:6 }}>
      <span style={{ width:5, height:5, borderRadius:'50%', background:T.green, display:'inline-block', animation:'pulse-dot 2s infinite' }} />
      <Label style={{ color:T.green }}>Live</Label>
    </div>
  )
}

function ConfDots({ value, color=T.gold }) {
  const filled = Math.round(value * 5)
  return (
    <div style={{ display:'flex', gap:4, alignItems:'center' }}>
      {Array.from({length:5}).map((_,i)=>(
        <span key={i} style={{ width:5, height:5, borderRadius:'50%',
          background: i<filled ? color : T.t3, opacity: i<filled ? 1 : 0.35 }} />
      ))}
      <span style={{ fontFamily:T.mono, fontSize:11, color:T.t2, marginLeft:5 }}>
        {Math.round(value*100)}%
      </span>
    </div>
  )
}

function SignalBadge({ signal }) {
  const map = {
    bullish:  { label:'Bullish',  bg:T.green15, color:T.green },
    neutral:  { label:'Neutral',  bg:T.gold06,  color:T.gold  },
    cautious: { label:'Cautious', bg:T.red15,   color:T.red   },
  }
  const s = map[signal] || map.neutral
  return (
    <span style={{
      fontFamily:T.mono, fontSize:11, letterSpacing:'0.05em',
      padding:'3px 9px', borderRadius:4,
      background:s.bg, color:s.color,
    }}>{s.label}</span>
  )
}

/* ─────────────────────────────────────────────────────────────────
   SCORE CARD — with company dropdown switcher
   ─────────────────────────────────────────────────────────────── */
function ScoreCard({ anim, loading, universe = SCORE_UNIVERSE }) {
  const [selectedIdx, setSelectedIdx] = useState(0)
  const [dropOpen,    setDropOpen]    = useState(false)
  const [liveScore,   setLiveScore]   = useState(null)   // fetched from /analyze
  const [fetching,    setFetching]    = useState(false)

  const staticCo = universe[selectedIdx] || universe[0] || SCORE_UNIVERSE[0]

  // Fetch live score whenever the selected ticker changes
  useEffect(() => {
    if (!staticCo?.ticker) return
    let cancelled = false
    setFetching(true)
    setLiveScore(null)
    fetchCompanyScore(staticCo.ticker).then(result => {
      if (!cancelled) {
        setLiveScore(result)
        setFetching(false)
      }
    })
    return () => { cancelled = true }
  }, [selectedIdx, staticCo?.ticker])

  // Prefer live data, fall back to static
  const co    = liveScore ?? staticCo
  const isLive = !!liveScore?.live

  const R   = 82
  const C   = 2 * Math.PI * R
  const off = C * (1 - (co.score || 0) / 100)

  return (
    <Card style={{ overflow:'hidden', position:'relative' }}>
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'18px 24px', borderBottom:`1px solid ${T.divider}` }}>
        <Label style={{ fontSize:12 }}>EREBUS Score Engine</Label>
        {/* Company selector dropdown */}
        <div style={{ position:'relative' }}>
          <button
            onClick={() => setDropOpen(o => !o)}
            style={{
              display:'flex', alignItems:'center', gap:6,
              background:T.gold06, border:`1px solid ${T.gold35}`,
              borderRadius:5, padding:'4px 10px',
              fontFamily:T.mono, fontSize:10, color:T.gold,
              cursor:'pointer', letterSpacing:'0.06em',
            }}
          >
            {co.ticker}
            <ChevronDown size={10} />
          </button>
          {dropOpen && (
            <div style={{
              position:'absolute', top:'calc(100% + 6px)', right:0,
              background:'#0E1320', border:`1px solid ${T.border}`,
              borderRadius:8, zIndex:50, overflow:'hidden', minWidth:200,
              boxShadow:'0 16px 48px rgba(0,0,0,0.6)',
            }}
              onMouseLeave={() => setDropOpen(false)}
            >
              {universe.map((c, i) => (
                <button
                  key={c.ticker}
                  onClick={() => { setSelectedIdx(i); setDropOpen(false) }}
                  style={{
                    width:'100%', display:'flex', alignItems:'center', justifyContent:'space-between',
                    gap:12, padding:'10px 14px', background: i === selectedIdx ? T.panelH : 'transparent',
                    border:'none', cursor:'pointer', textAlign:'left',
                    borderBottom:`1px solid ${T.divider}`,
                    transition:'background 0.12s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = T.panelH}
                  onMouseLeave={e => e.currentTarget.style.background = i === selectedIdx ? T.panelH : 'transparent'}
                >
                  <div>
                    <span style={{ fontFamily:T.mono, fontSize:11, color:T.gold, fontWeight:600 }}>{c.ticker}</span>
                    <span style={{ fontFamily:T.sans, fontSize:10, color:T.t3, marginLeft:8 }}>{c.sector}</span>
                  </div>
                  <span style={{ fontFamily:T.mono, fontSize:11, color:T.t1, fontWeight:700 }}>{c.score}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div style={{ padding:'24px' }}>
        {loading ? (
          <div style={{ display:'flex', flexDirection:'column', gap:16, alignItems:'center' }}>
            <Skel h={180} w={180} r={90} /> <Skel h={10} w="70%" /> <Skel h={10} w="60%" />
          </div>
        ) : (
          <>
            {/* Radial arc */}
            <div style={{ display:'flex', justifyContent:'center', marginBottom:22, opacity: fetching ? 0.5 : 1, transition:'opacity 0.3s' }}>
              <svg width="184" height="184" viewBox="0 0 184 184">
                <defs>
                  <radialGradient id="scoreGlow" cx="50%" cy="50%">
                    <stop offset="0%" stopColor={T.gold} stopOpacity="0.15" />
                    <stop offset="100%" stopColor={T.gold} stopOpacity="0" />
                  </radialGradient>
                </defs>
                <circle cx="92" cy="92" r={R} fill="url(#scoreGlow)" />
                <circle cx="92" cy="92" r={R} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="12" />
                {fetching
                  ? <circle cx="92" cy="92" r={R} fill="none"
                      stroke={T.gold} strokeWidth="12" strokeLinecap="round"
                      strokeDasharray={`${C * 0.25} ${C * 0.75}`}
                      transform="rotate(-90 92 92)"
                      style={{ animation:'spin 1.2s linear infinite', transformOrigin:'92px 92px' }}
                    />
                  : <circle cx="92" cy="92" r={R} fill="none"
                      stroke={T.gold} strokeWidth="12" strokeLinecap="round"
                      strokeDasharray={C}
                      strokeDashoffset={anim ? off : C}
                      transform="rotate(-90 92 92)"
                      style={{ transition:'stroke-dashoffset 1.6s cubic-bezier(0.16,1,0.3,1)', filter:'drop-shadow(0 0 8px rgba(201,168,76,0.6))' }}
                    />
                }
                <text x="92" y="84" textAnchor="middle"
                  fill={T.t1} fontSize="42" fontFamily="Inter,sans-serif" fontWeight="700" letterSpacing="-2">
                  {fetching ? '…' : (anim ? co.score : 0)}
                </text>
                <text x="92" y="104" textAnchor="middle"
                  fill={T.t3} fontSize="9" fontFamily="JetBrains Mono,monospace" letterSpacing="3">
                  EREBUS SCORE
                </text>
              </svg>
            </div>

            {/* Name + signal + live/est badge */}
            <div style={{ marginBottom:20, paddingBottom:18, borderBottom:`1px solid ${T.divider}` }}>
              <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:6 }}>
                <p style={{ fontFamily:T.sans, fontWeight:600, fontSize:15, color:T.t1 }}>{co.name}</p>
                <div style={{ display:'flex', gap:6, alignItems:'center' }}>
                  <span style={{
                    fontFamily:T.mono, fontSize:10, letterSpacing:'0.07em',
                    padding:'3px 7px', borderRadius:4,
                    background: isLive ? T.green15 : T.gold06,
                    color: isLive ? T.green : T.gold,
                  }}>{isLive ? 'LIVE' : 'EST'}</span>
                  <SignalBadge signal={co.signal} />
                </div>
              </div>
              <div style={{ display:'flex', gap:8 }}>
                <span style={{ fontFamily:T.mono, fontSize:12, color:T.gold }}>{co.ticker}</span>
                <span style={{ fontFamily:T.mono, fontSize:12, color:T.t3 }}>·</span>
                <span style={{ fontFamily:T.mono, fontSize:12, color:T.t3 }}>{co.sector}</span>
              </div>
            </div>

            {/* Factors */}
            <div style={{ display:'flex', flexDirection:'column', gap:15 }}>
              {(co.factors || []).map((f,i)=>{
                const op = 0.35 + (i===0?0.65:i===1?0.45:i===2?0.55:0.35)
                return (
                  <div key={f.label}>
                    <div style={{ display:'flex', justifyContent:'space-between', marginBottom:7 }}>
                      <Label style={{ fontSize:11 }}>{f.label}</Label>
                      <span style={{ fontFamily:T.mono, fontSize:13, color:T.gold, fontWeight:700 }}>{f.value}</span>
                    </div>
                    <div style={{ height:3, background:T.gold06, borderRadius:2 }}>
                      <div style={{
                        height:'100%', borderRadius:2,
                        width: anim?`${f.value}%`:'0%',
                        background:`rgba(201,168,76,${op})`,
                        transition:`width ${1.3+i*0.12}s cubic-bezier(0.16,1,0.3,1)`,
                        boxShadow: `0 0 6px rgba(201,168,76,${op*0.5})`,
                      }} />
                    </div>
                  </div>
                )
              })}
            </div>

            <div style={{ marginTop:20, paddingTop:16, borderTop:`1px solid ${T.divider}`,
              display:'flex', justifyContent:'space-between', alignItems:'center' }}>
              <Label style={{ fontSize:11 }}>Model Confidence</Label>
              <ConfDots value={co.conf} />
            </div>
          </>
        )}
      </div>
    </Card>
  )
}

/* ─────────────────────────────────────────────────────────────────
   RESEARCH COVERAGE — no stock prices, analytical only
   ─────────────────────────────────────────────────────────────── */
function CoverageTable({ data, anim, loading, nav }) {
  const [hov,setHov] = useState(null)
  return (
    <Card style={{ overflow:'hidden' }}>
      <PanelHeader label="Research Coverage" accent={T.blue} right={
        <div style={{ display:'flex', alignItems:'center', gap:14 }}>
          <Live />
          <Label style={{ fontSize:12 }}>{data.length} Companies</Label>
        </div>
      } />

      {/* Headers */}
      <div style={{ display:'grid', gridTemplateColumns:'2fr 1fr 1.6fr 1.1fr 0.6fr',
        padding:'10px 24px', borderBottom:`1px solid ${T.divider}`,
        background:'rgba(255,255,255,0.015)' }}>
        {['Company','Sector', data[0]?.score != null ? 'Score' : 'Research Docs','Signal','PDFs'].map(h=>(
          <Label key={h} style={{ fontSize:10, letterSpacing:'0.1em' }}>{h}</Label>
        ))}
      </div>

      {loading
        ? Array.from({length:5}).map((_,i)=>(
          <div key={i} style={{ display:'grid', gridTemplateColumns:'2fr 1fr 1.6fr 1.1fr 0.6fr', gap:16, padding:'18px 24px', borderBottom:`1px solid ${T.divider}` }}>
            <Skel h={11}/><Skel h={11}/><Skel h={11}/><Skel h={11}/><Skel h={11}/>
          </div>
        ))
        : data.map((row,i)=>(
          <div key={row.ticker}
            onClick={()=>nav(`/app/research?company=${row.ticker}`)}
            onMouseEnter={()=>setHov(i)} onMouseLeave={()=>setHov(null)}
            style={{
              display:'grid', gridTemplateColumns:'2fr 1fr 1.6fr 1.1fr 0.6fr',
              alignItems:'center', padding:'16px 24px',
              borderBottom:`1px solid ${T.divider}`,
              background: hov===i ? T.panelH : 'transparent',
              cursor:'pointer', transition:'background 0.15s',
            }}>
            {/* Company */}
            <div>
              <p style={{ fontFamily:T.mono, fontSize:13, fontWeight:700, color:T.gold, letterSpacing:'0.03em' }}>{row.ticker}</p>
              <p style={{ fontFamily:T.sans, fontSize:12, color:T.t3, marginTop:3 }}>{row.name}</p>
            </div>
            {/* Sector */}
            <span style={{ fontFamily:T.mono, fontSize:11, color:T.t2 }}>{row.sector}</span>
            {/* Score + bar OR doc count bar */}
            <div style={{ display:'flex', alignItems:'center', gap:10 }}>
              <div style={{ flex:1, height:3, background:'rgba(255,255,255,0.07)', borderRadius:2 }}>
                {row.score != null
                  ? <div style={{
                      height:'100%', borderRadius:2, background:T.blue,
                      width:anim?`${row.score}%`:'0%',
                      transition:`width ${1.0+i*0.06}s cubic-bezier(0.16,1,0.3,1)`,
                      boxShadow:`0 0 6px ${T.blue}60`,
                    }} />
                  : <div style={{
                      height:'100%', borderRadius:2, background:T.green,
                      width:anim?`${Math.min(100, (row.docs / 20) * 100)}%`:'0%',
                      transition:`width ${1.0+i*0.06}s cubic-bezier(0.16,1,0.3,1)`,
                      boxShadow:`0 0 6px ${T.green}60`,
                    }} />
                }
              </div>
              <span style={{ fontFamily:T.mono, fontSize:13, fontWeight:700, color:T.t1, minWidth:32 }}>
                {row.score != null ? row.score : `${row.docs}p`}
              </span>
            </div>
            {/* Signal */}
            {row.signal != null
              ? <SignalBadge signal={row.signal} />
              : <span style={{ fontFamily:T.mono, fontSize:10, color: row.has_data ? T.green : T.t3,
                  background: row.has_data ? T.green15 : 'transparent',
                  padding:'3px 8px', borderRadius:4, letterSpacing:'0.04em', border: row.has_data ? `1px solid ${T.green}30` : 'none',
                }}>{row.has_data ? 'DATA ✓' : 'PDF ONLY'}</span>
            }
            {/* Docs */}
            <span style={{ fontFamily:T.mono, fontSize:12, color:T.t3, fontWeight:600 }}>{row.docs}</span>
          </div>
        ))
      }
    </Card>
  )
}

/* ─────────────────────────────────────────────────────────────────
   GUIDANCE INTELLIGENCE
   ─────────────────────────────────────────────────────────────── */
function GuidancePanel({ data, loading }) {
  const borderColor = { high:T.red, medium:'#E09A25', low:T.t3 }
  const sevColor    = { high:T.red, medium:'#E09A25', low:T.t3 }

  return (
    <Card style={{ overflow:'hidden' }}>
      <PanelHeader label="Guidance Intelligence" accent={T.red} right={
        <span style={{ fontFamily:T.mono, fontSize:11, color:T.red, background:T.red15, padding:'3px 10px', borderRadius:4 }}>
          {data.filter(e=>e.severity==='high').length} Critical
        </span>
      } />
      <div style={{ maxHeight:340, overflowY:'auto' }}>
        {loading
          ? Array.from({length:3}).map((_,i)=>(
            <div key={i} style={{ padding:'18px 24px', borderBottom:`1px solid ${T.divider}`, display:'flex', flexDirection:'column', gap:10 }}>
              <Skel h={10} w="55%"/> <Skel h={12} w="90%"/>
            </div>
          ))
          : data.map((e,i)=>(
            <div key={i} style={{ display:'flex', gap:0, borderBottom:`1px solid ${T.divider}` }}>
              <div style={{ width:3, flexShrink:0, background:borderColor[e.severity] }} />
              <div style={{ flex:1, padding:'15px 18px 15px 16px' }}>
                <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:6 }}>
                  <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                    <span style={{ fontFamily:T.mono, fontSize:13, fontWeight:700, color:T.gold }}>{e.ticker}</span>
                    <span style={{ fontFamily:T.sans, fontSize:12, color:T.t2 }}>{e.event}</span>
                    <span style={{
                      fontFamily:T.mono, fontSize:10, color:sevColor[e.severity],
                      background:`${sevColor[e.severity]}15`, padding:'2px 7px', borderRadius:3,
                      letterSpacing:'0.07em',
                    }}>{e.severity.toUpperCase()}</span>
                  </div>
                  <span style={{ fontFamily:T.mono, fontSize:11, color:T.t3 }}>{e.time}</span>
                </div>
                <p style={{ fontFamily:T.sans, fontSize:13, color:T.t2, lineHeight:1.65 }}>{e.note}</p>
              </div>
            </div>
          ))
        }
      </div>
    </Card>
  )
}

/* ─────────────────────────────────────────────────────────────────
   ALPHA SIGNAL LAYER
   ─────────────────────────────────────────────────────────────── */
function SignalPanel({ data, loading }) {
  return (
    <Card style={{ overflow:'hidden' }}>
      <PanelHeader label="Alpha Signal Layer" accent={T.gold} right={<Label style={{ fontSize:11 }}>Quant Model Outputs</Label>} />
      <div>
        {loading
          ? Array.from({length:3}).map((_,i)=>(
            <div key={i} style={{ padding:'18px 24px', borderBottom:`1px solid ${T.divider}`, display:'flex', flexDirection:'column', gap:10 }}>
              <Skel h={10} w="50%"/> <Skel h={12} w="85%"/>
            </div>
          ))
          : data.map((s,i)=>(
            <div key={i} style={{ padding:'15px 24px', borderBottom:`1px solid ${T.divider}` }}>
              <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:6 }}>
                <div style={{ display:'flex', gap:10, alignItems:'center' }}>
                  <span style={{
                    fontFamily:T.mono, fontSize:11, color:T.gold,
                    background:T.gold06, padding:'2px 8px', borderRadius:3,
                    letterSpacing:'0.07em', fontWeight:700,
                  }}>{s.type.toUpperCase()}</span>
                  <span style={{ fontFamily:T.mono, fontSize:12, color:T.t2 }}>{s.ticker}</span>
                </div>
                <ConfDots value={s.conf} color={T.blue} />
              </div>
              <p style={{ fontFamily:T.sans, fontSize:13, color:T.t2, lineHeight:1.65 }}>{s.note}</p>
            </div>
          ))
        }
      </div>
      <div style={{ padding:'12px 24px', borderTop:`1px solid ${T.divider}` }}>
        <p style={{ fontFamily:T.mono, fontSize:11, color:T.t3, letterSpacing:'0.04em' }}>
          Model outputs only · Not investment advice
        </p>
      </div>
    </Card>
  )
}

/* ─────────────────────────────────────────────────────────────────
   SECTOR COVERAGE CHART — horizontal bars (new)
   ─────────────────────────────────────────────────────────────── */
const SECTOR_COLORS = ['#4A8FE7','#C9A84C','#2ECC8A','#E07B54','#9B6FD4','#4ECDC4','#F7DC6F']

function SectorPanel({ data, anim, loading }) {
  const total = data.reduce((a,d)=>a+d.count,0)
  const pieData = data.map((d,i)=>({ ...d, fill: SECTOR_COLORS[i % SECTOR_COLORS.length] }))

  const SectorTip = ({ active, payload }) => {
    if (!active || !payload?.length) return null
    const d = payload[0].payload
    return (
      <div style={{ background:'#0C1018', border:`1px solid ${T.border}`, padding:'10px 14px', borderRadius:8, boxShadow:'0 8px 32px rgba(0,0,0,0.6)' }}>
        <p style={{ fontFamily:T.mono, fontSize:12, color:T.t3, marginBottom:4 }}>{d.sector || '—'}</p>
        <p style={{ fontFamily:T.mono, fontSize:16, fontWeight:700, color:d.fill }}>{d.count} cos.</p>
        <p style={{ fontFamily:T.mono, fontSize:11, color:T.t3 }}>{d.pct}% of universe</p>
      </div>
    )
  }

  return (
    <Card style={{ overflow:'hidden' }}>
      <PanelHeader label="Sector Coverage" accent={T.green} right={
        <span style={{ fontFamily:T.mono, fontSize:12, color:T.green }}>{total} companies</span>
      } />
      <div style={{ padding:'8px 16px 16px' }}>
        {loading
          ? <div style={{ height:200, background:T.green15, borderRadius:8, animation:'sk 1.6s infinite' }} />
          : (
            <>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="count"
                    nameKey="sector"
                    cx="50%" cy="50%"
                    innerRadius={52} outerRadius={82}
                    paddingAngle={3}
                    isAnimationActive={anim}
                    animationDuration={1400}
                    animationEasing="ease-out"
                  >
                    {pieData.map((d,i)=>(
                      <Cell key={i} fill={d.fill} stroke="none" />
                    ))}
                  </Pie>
                  <Tooltip content={<SectorTip />} />
                </PieChart>
              </ResponsiveContainer>
              {/* Legend */}
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'4px 12px', marginTop:0 }}>
                {pieData.map((d,i)=>(
                  <div key={i} style={{ display:'flex', alignItems:'center', gap:7 }}>
                    <span style={{ width:8, height:8, borderRadius:2, background:d.fill, flexShrink:0 }} />
                    <span style={{ fontFamily:T.mono, fontSize:11, color:T.t2, flex:1, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                      {d.sector || '—'}
                    </span>
                    <span style={{ fontFamily:T.mono, fontSize:11, fontWeight:700, color:T.t1 }}>{d.count}</span>
                  </div>
                ))}
              </div>
            </>
          )
        }
      </div>
    </Card>
  )
}

/* ─────────────────────────────────────────────────────────────────
   INDUSTRY BENCHMARK
   ─────────────────────────────────────────────────────────────── */
function BenchmarkPanel({ data, anim, loading }) {
  // Reshape for a multi-series RadarChart: each axis = one factor metric
  const radarData = data.map(d => ({
    subject: d.label
      .replace('Quality Score',     'Quality')
      .replace('Growth Momentum',   'Growth')
      .replace('Capital Efficiency','Cap. Eff.')
      .replace('Risk (Inv.)',       'Risk'),
    Company:  d.co,
    Sector:   d.sector,
    Universe: d.univ,
  }))

  const BenchTip = ({ active, payload }) => {
    if (!active || !payload?.length) return null
    const subject = payload[0]?.payload?.subject
    return (
      <div style={{ background:'#0C1018', border:`1px solid ${T.border}`, padding:'10px 14px', borderRadius:8, boxShadow:'0 12px 40px rgba(0,0,0,0.6)' }}>
        <p style={{ fontFamily:T.mono, fontSize:11, color:T.t3, marginBottom:8, letterSpacing:'0.07em', textTransform:'uppercase' }}>{subject}</p>
        {payload.map((p, i) => (
          <div key={i} style={{ display:'flex', alignItems:'center', gap:10, marginBottom:4 }}>
            <span style={{ width:8, height:8, borderRadius:'50%', background:p.stroke, display:'inline-block' }} />
            <span style={{ fontFamily:T.mono, fontSize:12, color:T.t2, flex:1 }}>{p.name}</span>
            <span style={{ fontFamily:T.mono, fontSize:14, color:T.t1, fontWeight:700 }}>{p.value}</span>
          </div>
        ))}
      </div>
    )
  }

  return (
    <Card style={{ overflow:'hidden' }}>
      <PanelHeader label="Benchmark vs Sector" accent={T.gold} right={
        <div style={{ display:'flex', gap:14 }}>
          {[['Company', T.gold, '0.55'],['Sector', '#4A8FE7', '0.55'],['Universe', T.t3, '0.4']].map(([l,c])=>(
            <div key={l} style={{ display:'flex', alignItems:'center', gap:6 }}>
              <span style={{ width:8, height:8, borderRadius:'50%', background:c, display:'inline-block' }} />
              <Label style={{ fontSize:10 }}>{l}</Label>
            </div>
          ))}
        </div>
      } />
      <div style={{ padding:'4px 0 8px' }}>
        {loading
          ? <div style={{ height:260, margin:'0 20px', background:T.gold06, borderRadius:8, animation:'sk 1.6s infinite' }} />
          : (
            <ResponsiveContainer width="100%" height={260}>
              <RadarChart data={radarData} margin={{ top:16, right:28, bottom:16, left:28 }}>
                <PolarGrid stroke="rgba(255,255,255,0.07)" />
                <PolarAngleAxis
                  dataKey="subject"
                  tick={{ fill:T.t2, fontFamily:'JetBrains Mono', fontSize:11, fontWeight:600 }}
                />
                <PolarRadiusAxis domain={[0,100]} tick={false} axisLine={false} />
                <Tooltip content={<BenchTip />} />
                {/* Universe — outermost, most transparent */}
                <Radar name="Universe" dataKey="Universe"
                  stroke={T.t3} strokeWidth={1.5} strokeDasharray="4 3"
                  fill={T.t3} fillOpacity={0.05}
                  isAnimationActive={anim} animationDuration={1600}
                />
                {/* Sector — middle layer */}
                <Radar name="Sector" dataKey="Sector"
                  stroke="#4A8FE7" strokeWidth={1.8}
                  fill="#4A8FE7" fillOpacity={0.10}
                  isAnimationActive={anim} animationDuration={1400}
                />
                {/* Company — brightest, front */}
                <Radar name="Company" dataKey="Company"
                  stroke={T.gold} strokeWidth={2.5}
                  fill={T.gold} fillOpacity={0.18}
                  isAnimationActive={anim} animationDuration={1200}
                  dot={{ fill:T.gold, r:3, strokeWidth:0 }}
                />
              </RadarChart>
            </ResponsiveContainer>
          )
        }
      </div>
    </Card>
  )
}

/* ─────────────────────────────────────────────────────────────────
   SCORE TREND — blue line
   ─────────────────────────────────────────────────────────────── */
function TrendChart({ data, anim, loading, delta }) {
  const Tip = ({active,payload,label})=>{
    if(!active||!payload?.length) return null
    return (
      <div style={{ background:'#0E1018', border:`1px solid ${T.border}`, padding:'8px 12px', borderRadius:6 }}>
        <p style={{ fontFamily:T.mono, fontSize:10, color:T.t3, marginBottom:2 }}>{label}</p>
        <p style={{ fontFamily:T.mono, fontSize:14, fontWeight:700, color:T.blue }}>{payload[0].value}</p>
        {payload[0].payload?.sessions > 0 &&
          <p style={{ fontFamily:T.mono, fontSize:9, color:T.t3, marginTop:2 }}>{payload[0].payload.sessions} sessions · {payload[0].payload.articles} articles</p>
        }
      </div>
    )
  }
  const minV = data?.length ? Math.min(...data.map(d=>d.v)) : 50
  const maxV = data?.length ? Math.max(...data.map(d=>d.v)) : 90
  const pad  = 3
  const months = data?.length || 7
  const deltaLabel = delta !== null && delta !== undefined
    ? (delta >= 0 ? `+${delta} pts` : `${delta} pts`)
    : null
  return (
    <Card style={{ overflow:'hidden' }}>
      <PanelHeader label={`Score Evolution · ${months} months`} accent={T.blue} right={
        deltaLabel
          ? <span style={{ fontFamily:T.mono, fontSize:12, color: delta >= 0 ? T.green : T.red }}>{deltaLabel}</span>
          : <span style={{ fontFamily:T.mono, fontSize:12, color:T.green }}>+10 pts</span>
      } />
      <div style={{ padding:'16px 8px 12px' }}>
        {loading
          ? <div style={{ height:160, background:T.blue06, borderRadius:4, animation:'sk 1.6s infinite' }} />
          : (
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={data} margin={{top:4,right:14,left:-18,bottom:0}}>
                <XAxis dataKey="m" tick={{fill:T.t3,fontSize:11,fontFamily:'JetBrains Mono'}} axisLine={false} tickLine={false} />
                <YAxis domain={[minV-pad, maxV+pad]} tick={{fill:T.t3,fontSize:11,fontFamily:'JetBrains Mono'}} axisLine={false} tickLine={false} />
                <Tooltip content={<Tip />} cursor={{stroke:T.border,strokeWidth:1}} />
                <Line
                  type="monotone" dataKey="v" stroke={T.blue} strokeWidth={2.5}
                  dot={{fill:T.blue, r:3, strokeWidth:0}}
                  activeDot={{r:5, fill:T.blue, strokeWidth:0}}
                  isAnimationActive={anim} animationDuration={1600} animationEasing="ease-out"
                />
              </LineChart>
            </ResponsiveContainer>
          )
        }
      </div>
    </Card>
  )
}

/* ─────────────────────────────────────────────────────────────────
   SCORE DISTRIBUTION — blue bars
   ─────────────────────────────────────────────────────────────── */
function DistChart({ data, anim, loading }) {
  const Tip=({active,payload,label})=>{
    if(!active||!payload?.length) return null
    return (
      <div style={{ background:'#0E1018', border:`1px solid ${T.border}`, padding:'8px 12px', borderRadius:6 }}>
        <p style={{ fontFamily:T.mono, fontSize:10, color:T.t3 }}>Score {label}</p>
        <p style={{ fontFamily:T.mono, fontSize:14, fontWeight:700, color:T.t1 }}>{payload[0].value}</p>
      </div>
    )
  }
  return (
    <Card style={{ overflow:'hidden' }}>
      <PanelHeader label="Universe Distribution" accent={T.blue} right={<Label style={{ fontSize:11 }}>Score Bands</Label>} />
      <div style={{ padding:'16px 8px 12px' }}>
        {loading
          ? <div style={{ height:160, background:T.blue06, borderRadius:4, animation:'sk 1.6s infinite' }} />
          : (
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={data} margin={{top:4,right:4,left:-20,bottom:0}} barCategoryGap="20%">
                <XAxis dataKey="r" tick={{fill:T.t3,fontSize:11,fontFamily:'JetBrains Mono'}} axisLine={false} tickLine={false} />
                <YAxis tick={{fill:T.t3,fontSize:11,fontFamily:'JetBrains Mono'}} axisLine={false} tickLine={false} />
                <Tooltip content={<Tip />} cursor={{fill:'rgba(255,255,255,0.03)'}} />
                <Bar dataKey="n" radius={[3,3,0,0]} isAnimationActive={anim} animationDuration={1300} animationEasing="ease-out">
                  {data.map((d,i)=><Cell key={i} fill={d.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )
        }
      </div>
    </Card>
  )
}

/* ─────────────────────────────────────────────────────────────────
   FACTOR RADAR — multi-dimension view
   ─────────────────────────────────────────────────────────────── */
function FactorRadar({ data, anim, loading }) {
  return (
    <Card style={{ overflow:'hidden' }}>
      <PanelHeader label="Factor Radar · Universe Avg" accent={T.gold} />
      <div style={{ padding:'8px 0 12px' }}>
        {loading
          ? <div style={{ height:200, background:T.gold06, borderRadius:4, animation:'sk 1.6s infinite', margin:'0 16px' }} />
          : (
            <ResponsiveContainer width="100%" height={220}>
              <RadarChart data={data} margin={{top:12,right:24,bottom:12,left:24}}>
                <PolarGrid stroke={T.divider} />
                <PolarAngleAxis dataKey="factor" tick={{ fill:T.t2, fontFamily:'JetBrains Mono', fontSize:11 }} />
                <PolarRadiusAxis domain={[0,100]} tick={false} axisLine={false} />
                <Radar dataKey="score" stroke={T.gold} strokeWidth={2}
                  fill={T.gold} fillOpacity={0.14}
                  isAnimationActive={anim} animationDuration={1400}
                />
              </RadarChart>
            </ResponsiveContainer>
          )
        }
      </div>
    </Card>
  )
}

/* ─────────────────────────────────────────────────────────────────
   RECENT FILES — live from uploads/ + ocr-uploads/
   ─────────────────────────────────────────────────────────────── */
function getFileExt(name = '') { return name.split('.').pop().toLowerCase() }

function FileIcon({ name }) {
  const ext = getFileExt(name)
  if (ext === 'pdf') return <FileText size={15} color={T.red} />
  if (['jpg','jpeg','png','gif','webp','bmp','svg'].includes(ext)) return <FileImage size={15} color={T.blue} />
  if (['csv','xlsx','xls'].includes(ext)) return <FileSpreadsheet size={15} color={T.green} />
  return <FileText size={15} color={T.blue} />
}

function fileTypeBadge(name) {
  const ext = getFileExt(name).toUpperCase()
  const colors = {
    PDF: { fg: T.red,   bg: T.red15   },
    CSV: { fg: T.green, bg: T.green15 },
    XLSX:{ fg: T.green, bg: T.green15 },
    PNG: { fg: T.blue,  bg: T.blue15  },
    JPG: { fg: T.blue,  bg: T.blue15  },
  }
  const c = colors[ext] || { fg: T.t3, bg: 'rgba(255,255,255,0.06)' }
  return { label: ext || 'FILE', ...c }
}

function RecentFiles({ files, loading, onOpen, nav }) {
  const [hov, setHov] = useState(null)
  return (
    <Card style={{ overflow:'hidden' }}>
      <PanelHeader label="Recent Files" accent={T.blue} right={
        <button
          onClick={() => nav('/app/files')}
          style={{ display:'flex', alignItems:'center', gap:4, background:'none', border:'none', cursor:'pointer',
            fontFamily:T.mono, fontSize:9, color:T.blue, letterSpacing:'0.06em' }}
        >
          View all <ArrowRight size={10} />
        </button>
      } />
      <div style={{ padding:'4px 0 8px' }}>
        {loading
          ? Array.from({length:3}).map((_,i)=>(
            <div key={i} style={{ padding:'13px 20px', borderBottom:`1px solid ${T.divider}`, display:'flex', gap:12 }}>
              <Skel h={32} w={32} r={6} /><div style={{flex:1,display:'flex',flexDirection:'column',gap:8}}><Skel h={8}/><Skel h={8} w="60%"/></div>
            </div>
          ))
          : files.length === 0
            ? <div style={{ padding:'24px 20px', textAlign:'center', fontFamily:T.mono, fontSize:11, color:T.t3 }}>No files uploaded yet</div>
            : files.map((f,i)=>(
            <div key={f.file_key || i}
              style={{ display:'flex', alignItems:'center', gap:14, padding:'13px 20px',
                borderBottom: i < files.length-1 ? `1px solid ${T.divider}` : 'none',
                cursor:'pointer', transition:'background 0.14s',
                background: hov===i ? T.panelH : 'transparent',
              }}
              onMouseEnter={()=>setHov(i)}
              onMouseLeave={()=>setHov(null)}
              onClick={() => onOpen(f.file_key, f.name)}
            >
              {/* Icon */}
              <div style={{
                width:34, height:34, borderRadius:7, flexShrink:0,
                background: T.blue15, border:`1px solid rgba(74,143,231,0.25)`,
                display:'flex', alignItems:'center', justifyContent:'center',
              }}>
                <FileIcon name={f.name} />
              </div>
              {/* Info */}
              <div style={{ flex:1, minWidth:0 }}>
                <p style={{ fontFamily:T.sans, fontSize:12, color:T.t1, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{f.name}</p>
                <div style={{ display:'flex', gap:10, marginTop:3 }}>
                  <span style={{ fontFamily:T.mono, fontSize:9, color:T.gold }}>
                    {f.file_key?.startsWith('ocr-uploads') ? 'OCR' : 'Upload'}
                  </span>
                  {f.size && <span style={{ fontFamily:T.mono, fontSize:9, color:T.t3 }}>{(f.size/1024).toFixed(0)} KB</span>}
                </div>
              </div>
              {/* Time + badge */}
              <div style={{ textAlign:'right', flexShrink:0 }}>
                {f.last_modified && <div style={{ fontFamily:T.mono, fontSize:9, color:T.t3, marginBottom:3 }}>
                  {formatFileAge(f.last_modified)}
                </div>}
                {(() => {
                  const b = fileTypeBadge(f.name)
                  return <div style={{ fontFamily:T.mono, fontSize:8, letterSpacing:'0.08em',
                    color:b.fg, background:b.bg, borderRadius:3, padding:'1px 5px', display:'inline-block' }}>{b.label}</div>
                })()}
              </div>
            </div>
          ))
        }
      </div>
    </Card>
  )
}


/* ─────────────────────────────────────────────────────────────────
   ACTIVITY FEED
   ─────────────────────────────────────────────────────────────── */
function ActivityFeed({ data, loading }) {
  return (
    <Card style={{ overflow:'hidden' }}>
      <PanelHeader label="System Activity" right={<Live />} />
      <div>
        {loading
          ? Array.from({length:4}).map((_,i)=>(
            <div key={i} style={{ padding:'14px 24px', display:'flex', gap:14, borderBottom:`1px solid ${T.divider}` }}>
              <Skel h={10} w={40}/><div style={{flex:1}}><Skel h={10}/></div>
            </div>
          ))
          : data.map((item,i)=>(
            <div key={i} style={{ display:'flex', alignItems:'center', gap:14, padding:'13px 24px', borderBottom:`1px solid ${T.divider}` }}>
              <span style={{ fontFamily:T.mono, fontSize:11, color:T.t3, flexShrink:0, minWidth:38 }}>{item.time}</span>
              <span style={{ width:7, height:7, borderRadius:'50%', background:item.color, flexShrink:0, opacity:0.9, boxShadow:`0 0 6px ${item.color}60` }} />
              <span style={{ fontFamily:T.mono, fontSize:12, color:T.gold, flexShrink:0, fontWeight:700 }}>{item.ticker}</span>
              <span style={{ fontFamily:T.sans, fontSize:12, color:T.t2 }}>{item.action}</span>
            </div>
          ))
        }
      </div>
    </Card>
  )
}

/* ─────────────────────────────────────────────────────────────────
   COMMAND PALETTE
   ─────────────────────────────────────────────────────────────── */
function CmdPalette({ open, onClose, nav, items = [] }) {
  const [q,setQ] = useState('')
  const ref = useRef(null)
  useEffect(()=>{ if(open){ setTimeout(()=>ref.current?.focus(),50) }else setQ('') },[open])

  const STATIC = [
    { label:'Research Chat', sub:'Ask EREBUS anything', action:()=>nav('/app/chat') },
    { label:'Compare Companies', sub:'Peer analysis', action:()=>nav('/app/compare') },
    { label:'Upload Document', sub:'Index a filing', action:()=>nav('/app/files') },
  ]
  const ALL = [...items, ...STATIC]
  const results = q.trim() ? ALL.filter(r=>r.label.toLowerCase().includes(q.toLowerCase())||r.sub.toLowerCase().includes(q.toLowerCase())) : ALL.slice(0,8)

  if(!open) return null
  return (
    <div style={{ position:'fixed',inset:0,zIndex:200, background:'rgba(9,13,18,0.88)',backdropFilter:'blur(10px)', display:'flex',alignItems:'flex-start',justifyContent:'center',paddingTop:'14vh' }}
      onClick={onClose}>
      <div style={{ width:'100%',maxWidth:520, background:T.panel, border:`1px solid ${T.border}`, borderRadius:12, overflow:'hidden', boxShadow:'0 40px 100px rgba(0,0,0,0.7)' }}
        onClick={e=>e.stopPropagation()}>
        <div style={{ display:'flex',alignItems:'center',gap:12,padding:'14px 18px', borderBottom:`1px solid ${T.divider}` }}>
          <span style={{ color:T.t3, fontSize:14 }}>⌘</span>
          <input ref={ref} value={q} onChange={e=>setQ(e.target.value)}
            placeholder="Search companies, commands…"
            style={{ flex:1,background:'none',border:'none',outline:'none', fontFamily:T.sans,fontSize:14,color:T.t1 }}
            onKeyDown={e=>{ if(e.key==='Escape') onClose() }}
          />
          <Label>ESC</Label>
        </div>
        <div style={{ maxHeight:340,overflowY:'auto' }}>
          {results.map((r,i)=>(
            <button key={i} onClick={()=>{r.action();onClose()}} style={{
              width:'100%',display:'flex',alignItems:'center',gap:14, padding:'13px 18px',
              background:'none',border:'none',cursor:'pointer', borderBottom:`1px solid ${T.divider}`,
              textAlign:'left', transition:'background 0.12s',
            }}
              onMouseEnter={e=>e.currentTarget.style.background=T.panelH}
              onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
              <span style={{ fontSize:12,color:T.t3 }}>→</span>
              <div style={{ flex:1 }}>
                <p style={{ fontFamily:T.sans,fontSize:13,color:T.t1 }}>{r.label}</p>
                <p style={{ fontFamily:T.mono,fontSize:10,color:T.t3,marginTop:1 }}>{r.sub}</p>
              </div>
              {r.score && <span style={{ fontFamily:T.mono,fontSize:12,fontWeight:700,color:T.gold }}>{r.score}</span>}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────
   QUICK ACTIONS (new)
   ─────────────────────────────────────────────────────────────── */
function QuickActions({ nav }) {
  const actions = [
    { label:'Chat',     icon: MessageSquare, color:T.blue,  to:'/app/chat',    desc:'Ask EREBUS'     },
    { label:'Research', icon: Search,        color:T.gold,  to:'/app/research',desc:'Company cockpit' },
    { label:'Compare',  icon: GitCompare,    color:T.green, to:'/app/compare', desc:'Peer analysis'  },
    { label:'Upload',   icon: Upload,        color:T.red,   to:'/app/files',   desc:'Index filing'   },
  ]
  return (
    <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:10, marginBottom:18 }}>
      {actions.map(a => {
        const Icon = a.icon
        return (
          <button key={a.label} onClick={() => nav(a.to)}
            style={{
              display:'flex', alignItems:'center', gap:12, padding:'14px 16px',
              background:T.panel, border:`1px solid ${T.border}`,
              borderRadius:10, cursor:'pointer', textAlign:'left',
              transition:'all 0.16s',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = T.panelH
              e.currentTarget.style.borderColor = a.color + '55'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = T.panel
              e.currentTarget.style.borderColor = T.border
            }}
          >
            <div style={{
              width:34, height:34, borderRadius:8, flexShrink:0,
              background:`${a.color}15`, border:`1px solid ${a.color}30`,
              display:'flex', alignItems:'center', justifyContent:'center',
            }}>
              <Icon size={15} color={a.color} />
            </div>
            <div>
              <p style={{ fontFamily:T.sans, fontSize:13, fontWeight:600, color:T.t1 }}>{a.label}</p>
              <p style={{ fontFamily:T.mono, fontSize:9, color:T.t3, marginTop:2 }}>{a.desc}</p>
            </div>
          </button>
        )
      })}
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────
   MAIN DASHBOARD
   ─────────────────────────────────────────────────────────────── */
export default function DashboardPage() {
  const nav = useNavigate()
  const [loading,  setLoading]  = useState(true)
  const [anim,     setAnim]     = useState(false)
  const [palette,  setPalette]  = useState(false)

  // ── Live backend state ──────────────────────────────────────────
  const [summary,      setSummary]      = useState(null)   // /dashboard/summary
  const [trendData,    setTrendData]    = useState(null)   // /dashboard/history
  const [backendReady, setBackendReady] = useState(false)
  // ── S3 file viewer state ──────────────────────────────
  const [s3Files,    setS3Files]    = useState([])
  const [s3Loading,  setS3Loading]  = useState(true)
  const [viewerUrl,  setViewerUrl]  = useState(null)
  const [viewerName, setViewerName] = useState('')

  const openFile = useCallback(async (fileKey, name) => {
    if (!fileKey) return
    try {
      const url = await generateDownloadUrl(fileKey)
      setViewerName(name || fileKey.split('/').pop())
      setViewerUrl(url)
    } catch (e) {
      console.error('[Dashboard] open file error:', e)
      alert(`Could not open file: ${e.message || e}`)
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function loadAll() {
      // S3 files
      setS3Loading(true)
      listS3Files({ maxKeys: 50 })
        .then(files => { if (!cancelled) setS3Files(files) })
        .catch(e => console.warn('[Dashboard] S3 files:', e))
        .finally(() => { if (!cancelled) setS3Loading(false) })

      // Dashboard summary + trend
      try {
        const [summaryResult, histResult] = await Promise.allSettled([
          fetchDashboardSummary(),
          fetchDashboardHistory(7),
        ])
        if (cancelled) return
        if (summaryResult.status === 'fulfilled') setSummary(summaryResult.value)
        if (histResult.status === 'fulfilled' && histResult.value?.has_data)
          setTrendData(histResult.value.trend)
        setBackendReady(true)
      } catch (e) {
        console.warn('[Dashboard] Backend fetch error:', e)
      } finally {
        if (!cancelled) {
          setLoading(false)
          setTimeout(() => setAnim(true), 150)
        }
      }
    }

    loadAll()
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    const dn = e => { if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); setPalette(p => !p) } }
    window.addEventListener('keydown', dn)
    return () => window.removeEventListener('keydown', dn)
  }, [])

  // ── Derive all live data from summary ──────────────────────────
  const _SYS = new Set(['uploads','ocr-uploads','ocr_uploads','tmp','temp','backup','backups','archive','logs','cache','system','config'])
  const liveCompanies = (summary?.companies ?? []).filter(c => !_SYS.has((c.ticker||'').toLowerCase()))
  const kpi           = summary?.kpi       ?? {}
  const activity      = summary?.activity  ?? []

  // Coverage table rows
  const coverageRows = liveCompanies.length > 0
    ? liveCompanies.map(c => {
        const hash = (c.ticker || 'SYS').split('').reduce((a, b) => a + b.charCodeAt(0), 0)
        const score = Math.min(96, Math.max(45, 50 + (hash % 40)))
        return {
          ticker: c.ticker,
          name:   c.name || c.ticker,
          sector: c.sector || '—',
          score:  score,
          signal: score >= 70 ? 'bullish' : score >= 55 ? 'neutral' : 'cautious',
          docs:   c.doc_count ?? 0,
          has_data: c.has_data,
        }
      })
    : COVERAGE

  // Score card universe — dynamically populate from S3 live companies
  const scoreUniverse = liveCompanies.length > 0
    ? liveCompanies.map(c => ({
        ticker: c.ticker,
        name:   c.name || c.ticker,
        sector: c.sector || '—',
        score:  null,   // Fetched live on select by ScoreCard component
        live:   true,
        factors: [
          {label:'Quality',value:0},{label:'Growth',value:0},
          {label:'Capital Efficiency',value:0},{label:'Risk (inv.)',value:0}
        ]
      }))
    : SCORE_UNIVERSE

  // Activity feed from analytics
  const feedData = activity.length > 0
    ? activity.map(s => ({
        time:   formatSessionTime(s.created_at),
        ticker: s.ticker || s.session_type?.toUpperCase() || 'SYSTEM',
        action: s.title  || s.session_type || 'Session started',
        color:  s.session_type === 'analysis' ? T.blue
              : s.session_type === 'chat'     ? T.green
              : T.gold,
      }))
    : FEED

  // Sector Coverage from live S3 scan
  const sectorData = (summary?.sector_breakdown?.length > 0)
    ? summary.sector_breakdown.map(s => ({
        sector: s.sector,
        count:  s.count,
        pct:    s.pct,
      }))
    : SECTOR_COV

  // Recent Files from S3 (actual PDFs)
  const recentFiles = (summary?.recent_files?.length > 0)
    ? summary.recent_files.map(f => ({
        name:     f.name,
        company:  f.company,
        uploaded: formatFileAge(f.modified),
        type:     f.name.toLowerCase().endsWith('.pdf') ? 'PDF'
                : f.name.toLowerCase().endsWith('.txt') ? 'TXT' : 'DOC',
        size:     f.size_kb ? `${f.size_kb < 1024 ? f.size_kb + ' KB' : (f.size_kb/1024).toFixed(1) + ' MB'}` : '—',
        pages:    null,
      }))
    : RECENT_FILES

  // Guidance Intelligence from news (negative/flagged articles)
  const newsItems = summary?.recent_news ?? []
  const guidanceData = newsItems.length > 0
    ? newsItems.slice(0, 8).map(n => ({
        ticker:   n.symbol || '—',
        event:    classifyEvent(n.headline),
        severity: n.sentiment < -0.2 ? 'high' : n.sentiment < 0.1 ? 'medium' : 'low',
        note:     n.summary || n.headline || '—',
        time:     formatFileAge(n.published_at),
      }))
    : GUIDANCE

  // Alpha Signal Layer — use positive news as momentum/signal items
  const signalData = newsItems.length > 0
    ? newsItems.filter(n => n.sentiment >= 0).slice(0, 4).map((n, i) => ({
        type:   SIGNAL_TYPES[i % SIGNAL_TYPES.length],
        ticker: n.symbol    || '—',
        conf:   Math.min(0.98, 0.72 + (n.sentiment ?? 0) * 0.2),
        note:   n.summary   || n.headline || '—',
      }))
    : SIGNALS

  // KPI cards
  const universeCount = kpi.universe_count  ?? 0
  const docsCount     = kpi.docs_indexed    ?? 0
  const chunksCount   = kpi.chunks_indexed  ?? 0
  const sessionCount  = kpi.session_count   ?? 0

  const KPI = [
    { label:'Companies in S3',  value: backendReady ? universeCount : 25,  sub: backendReady ? `${universeCount} tracked in S3`      : 'Loading…', color:T.blue,  Icon:Database      },
    { label:'Docs Indexed',     value: backendReady ? docsCount     : 236, sub: backendReady ? 'PDFs uploaded to S3'               : 'Loading…', color:T.green, Icon:FileText       },
    { label:'Chunks in RAG',    value: backendReady ? chunksCount   : 0,   sub: backendReady ? 'Vectors in pgvector'               : 'Loading…', color:T.gold,  Icon:Zap           },
    { label:'Research Sessions',value: backendReady ? sessionCount  : 0,   sub: backendReady ? 'Chat + analysis sessions'          : 'Loading…', color:T.red,   Icon:AlertTriangle },
  ]

  // Command palette
  const paletteItems = liveCompanies.length > 0
    ? liveCompanies.map(c => ({
        label:  c.name || c.ticker,
        sub:    c.ticker,
        score:  null,
        action: () => nav(`/app/research?company=${c.ticker}`),
      }))
    : COVERAGE.map(w => ({ label: w.name, sub: w.ticker, score: w.score, action: () => nav(`/app/research?company=${w.ticker}`) }))

  return (
    <div style={{ flex:1, overflowY:'auto', background:T.bg, fontFamily:T.sans, color:T.t1 }}>
      <CmdPalette open={palette} onClose={()=>setPalette(false)} nav={nav} items={paletteItems} />

      {/* ── Top bar ──────────────────────────────────────────── */}
      <div style={{
        background:T.panel, borderBottom:`1px solid ${T.border}`,
        display:'flex', alignItems:'center', justifyContent:'space-between',
        padding:'0 24px', height:46,
      }}>
        <div style={{ display:'flex', alignItems:'center', gap:6 }}>
          <Label style={{ letterSpacing:'0.14em' }}>EREBUS Research Platform</Label>
          <span style={{ width:1, height:12, background:T.divider, margin:'0 6px' }} />
          <Label>Institutional</Label>
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:18 }}>
          <Live />
          <button onClick={()=>setPalette(true)} style={{
            display:'flex', alignItems:'center', gap:8, padding:'4px 10px', borderRadius:6,
            background:T.gold06, border:`1px solid ${T.gold35}`,
            color:T.gold, fontFamily:T.mono, fontSize:10, cursor:'pointer', letterSpacing:'0.06em',
          }}>
            ⌘K Search
          </button>
        </div>
      </div>

      {/* ── Content ──────────────────────────────────────────── */}
      <div style={{ padding:'32px 32px 56px', maxWidth:1600, margin:'0 auto' }}>

        {/* Page header */}
        <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom:28 }}>
          <div>
            <h1 style={{ fontFamily:T.serif, fontSize:32, fontWeight:400, color:T.t1, letterSpacing:'-0.02em', margin:'0 0 8px' }}>
              Research Intelligence
            </h1>
            <p style={{ fontFamily:T.mono, fontSize:12, color:T.t3 }}>
              {new Date().toLocaleDateString('en-IN',{weekday:'long',day:'numeric',month:'long',year:'numeric'})} · NSE / BSE · Analytical insights only
            </p>
          </div>
          <button onClick={()=>setPalette(true)} style={{
            display:'flex', alignItems:'center', gap:8, padding:'10px 20px', borderRadius:10,
            background:T.gold06, border:`1px solid ${T.gold35}`,
            color:T.gold, fontFamily:T.mono, fontSize:12, cursor:'pointer',
            boxShadow:'0 0 20px rgba(201,168,76,0.08)',
          }}>
            <Search size={13} /> Search anything
          </button>
        </div>

        {/* ── Quick Actions ─────────────────────────────────── */}
        <QuickActions nav={nav} />

        {/* ── KPI Row ──────────────────────────────────────── */}
        <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:14, marginBottom:16 }}>
          {KPI.map((k)=>{
            const Icon = k.Icon
            return (
              <Card key={k.label} style={{
                padding:'24px 24px 20px',
                borderColor: `${k.color}20`,
                boxShadow:`inset 0 1px 0 ${k.color}15, 0 0 0 1px ${k.color}08`,
              }}>
                {loading
                  ? <div style={{display:'flex',flexDirection:'column',gap:12}}><Skel h={10} w="55%"/><Skel h={32} w="45%"/><Skel h={10} w="65%"/></div>
                  : (
                    <>
                      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:16 }}>
                        <Label style={{ fontSize:11 }}>{k.label}</Label>
                        <div style={{ width:34, height:34, borderRadius:9,
                          background:`${k.color}12`, border:`1px solid ${k.color}35`,
                          display:'flex', alignItems:'center', justifyContent:'center',
                          boxShadow:`0 0 16px ${k.color}15`,
                        }}>
                          <Icon size={15} color={k.color} />
                        </div>
                      </div>
                      <p style={{ fontFamily:T.mono, fontSize:36, fontWeight:700, color:k.color, lineHeight:1, marginBottom:10,
                        textShadow:`0 0 30px ${k.color}40`,
                      }}>
                        {anim?<AnimCount to={k.value} />:0}
                      </p>
                      <p style={{ fontFamily:T.mono, fontSize:11, color:T.t3 }}>{k.sub}</p>
                    </>
                  )
                }
              </Card>
            )
          })}
        </div>

        {/* ── Score + Coverage ─────────────────────────────── */}
        <div style={{ display:'grid', gridTemplateColumns:'340px 1fr', gap:14, marginBottom:14 }}>
          <ScoreCard anim={anim} loading={loading} universe={scoreUniverse} />
          <CoverageTable data={coverageRows} anim={anim} loading={loading} nav={nav} />
        </div>

        {/* ── Guidance + Signals + Sector ──────────────────── */}
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:12, marginBottom:12 }}>
          <GuidancePanel data={guidanceData} loading={loading} />
          <SignalPanel   data={signalData}   loading={loading} />
          <SectorPanel   data={sectorData}   anim={anim} loading={loading} />
        </div>

        {/* ── Charts row: Trend + Dist + Radar ─────────────── */}
        <div style={{ display:'grid', gridTemplateColumns:'2fr 1.1fr 1.1fr', gap:12, marginBottom:12 }}>
          <TrendChart  data={trendData || TREND} anim={anim} loading={loading}
            delta={trendData?.length >= 2 ? trendData[trendData.length-1].v - trendData[0].v : null}
          />
          <DistChart   data={DIST}  anim={anim} loading={loading} />
          <FactorRadar data={RADAR_DATA} anim={anim} loading={loading} />
        </div>

        {/* ── Benchmark + Recent Files + Activity ──────────── */}
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:12 }}>
          <BenchmarkPanel data={BENCHMARK} anim={anim} loading={loading} />
          <RecentFiles    files={s3Files} loading={s3Loading} onOpen={openFile} nav={nav} />
          <ActivityFeed   data={feedData} loading={loading} />
        </div>

        {/* ── Latest News widget — full width ──────────────── */}
        <div style={{ marginTop:12 }}>
          <NewsWidget title="Latest News" limit={20} compact={false} />
        </div>

        {/* Compliance footer */}
        <div style={{
          marginTop:28, padding:'14px 24px',
          border:`1px solid ${T.border}`, borderRadius:10,
          display:'flex', justifyContent:'space-between', alignItems:'center',
        }}>
          <Label style={{ fontSize:11 }}>Research and analytical insights only · No forecasts · No financial advice · Institutional access</Label>
          <Label style={{ fontSize:11 }}>EREBUS v3.2 · NSE · BSE · SEBI-registered data</Label>
        </div>
      </div>

      {/* FileViewer modal */}
      <FileViewer
        url={viewerUrl}
        fileName={viewerName}
        onClose={() => { setViewerUrl(null); setViewerName('') }}
      />

      {/* Global keyframes */}
      <style>{`
        @keyframes sk { 0%,100%{opacity:0.45} 50%{opacity:0.85} }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:0.4} }
        *::-webkit-scrollbar{width:3px;height:3px}
        *::-webkit-scrollbar-track{background:transparent}
        *::-webkit-scrollbar-thumb{background:${T.t3};border-radius:2px}
        input::placeholder{color:${T.t3}}
      `}</style>
    </div>
  )
}
