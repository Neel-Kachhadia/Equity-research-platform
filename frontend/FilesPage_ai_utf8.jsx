// src/pages/app/FilesPage.jsx ΓÇö EREBUS Sources Visualization
// Powered by GET /uploads/sources (live S3 + pgvector)

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Database, FileText, BarChart2, Search, RefreshCw,
  ChevronDown, ChevronRight, Download, Loader2,
  AlertCircle, CheckCircle, Layers, Filter,
  File, FileSpreadsheet, Code2, Image as ImageIcon,
  ExternalLink, Box,
} from 'lucide-react'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

/* ΓöÇΓöÇ Design tokens ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */
const T = {
  bg:       '#07090E',
  panel:    '#0F1420',
  panelH:   '#141929',
  border:   'rgba(255,255,255,0.07)',
  divider:  'rgba(255,255,255,0.045)',
  blue:     '#4A8FE7',
  green:    '#22C55E',
  gold:     '#C9A84C',
  red:      '#E7534A',
  t1:       '#E8ECF4',
  t2:       '#8B93A8',
  t3:       '#4A5166',
  mono:     "'JetBrains Mono', monospace",
  sans:     "'Inter', sans-serif",
}

/* ΓöÇΓöÇ File type config ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */
const FTYPE = {
  PDF:   { color: T.red,   Icon: FileText,       label: 'PDF'   },
  EXCEL: { color: T.green, Icon: FileSpreadsheet, label: 'XLSX'  },
  CSV:   { color: T.green, Icon: BarChart2,       label: 'CSV'   },
  JSON:  { color: T.blue,  Icon: Code2,           label: 'JSON'  },
  TXT:   { color: T.t2,    Icon: FileText,        label: 'TXT'   },
  IMAGE: { color: T.gold,  Icon: ImageIcon,       label: 'IMG'   },
  OTHER: { color: T.t3,    Icon: File,            label: 'FILE'  },
}

/* ΓöÇΓöÇ Formatters ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */
function fmtBytes(b) {
  if (!b) return 'ΓÇö'
  if (b < 1024)        return `${b} B`
  if (b < 1048576)     return `${(b/1024).toFixed(1)} KB`
  if (b < 1073741824)  return `${(b/1048576).toFixed(1)} MB`
  return `${(b/1073741824).toFixed(2)} GB`
}

function fmtAge(iso) {
  if (!iso) return 'ΓÇö'
  try {
    const d = Date.now() - new Date(iso).getTime()
    const m = Math.floor(d / 60000)
    if (m < 2)   return 'Just now'
    if (m < 60)  return `${m}m ago`
    const h = Math.floor(m / 60)
    if (h < 24)  return `${h}h ago`
    const dy = Math.floor(h / 24)
    if (dy < 7)  return `${dy}d ago`
    return new Date(iso).toLocaleDateString('en-IN', { day:'numeric', month:'short' })
  } catch { return 'ΓÇö' }
}

/* ΓöÇΓöÇ Pill badge ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */
function Pill({ label, color, bg }) {
  return (
    <span style={{
      fontFamily: T.mono, fontSize: 9, letterSpacing: '0.06em',
      padding: '2px 6px', borderRadius: 3,
      background: bg ?? `${color}18`, color,
    }}>{label}</span>
  )
}

/* ΓöÇΓöÇ Stats bar ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */
function StatsBar({ totals, loading }) {
  const stats = [
    { label: 'Companies',    value: totals?.companies   ?? 0, color: T.blue,  Icon: Box       },
    { label: 'Research PDFs',value: totals?.pdfs        ?? 0, color: T.red,   Icon: FileText  },
    { label: 'Total Files',  value: totals?.files       ?? 0, color: T.gold,  Icon: Database  },
    { label: 'Chunks in RAG',value: totals?.chunks      ?? 0, color: T.green, Icon: Layers    },
    { label: 'Storage',      value: fmtBytes(totals?.total_bytes), color: T.t2, Icon: BarChart2 },
  ]
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: 'repeat(5,1fr)', gap: 10, marginBottom: 20,
    }}>
      {stats.map(s => {
        const Icon = s.Icon
        return (
          <div key={s.label} style={{
            background: T.panel, border: `1px solid ${T.border}`,
            borderRadius: 10, padding: '14px 16px',
          }}>
            {loading
              ? <div style={{ height: 28, background: `${s.color}15`, borderRadius: 4, animation: 'sk 1.6s infinite' }} />
              : <>
                  <div style={{ display:'flex', alignItems:'center', gap:6, marginBottom:6 }}>
                    <Icon size={12} color={s.color} />
                    <span style={{ fontFamily: T.mono, fontSize: 9, color: T.t3, letterSpacing: '0.05em' }}>{s.label.toUpperCase()}</span>
                  </div>
                  <p style={{ fontFamily: T.mono, fontSize: 22, fontWeight: 700, color: s.color }}>{s.value}</p>
                </>
            }
          </div>
        )
      })}
    </div>
  )
}

/* ΓöÇΓöÇ File row inside expanded company ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */
function FileRow({ file, onDownload }) {
  const [loading, setLoading] = useState(false)
  const ft = FTYPE[file.file_type] ?? FTYPE.OTHER
  const FIcon = ft.Icon

  async function download() {
    setLoading(true)
    try {
      const res = await fetch(`${API}/uploads/generate-download-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_key: file.file_key }),
      })
      const { download_url } = await res.json()
      window.open(download_url, '_blank', 'noreferrer')
    } catch { alert('Could not get download link') }
    setLoading(false)
  }

  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '1fr 72px 80px 60px 36px',
      alignItems: 'center', padding: '9px 16px',
      borderBottom: `1px solid ${T.divider}`,
    }}>
      {/* Name */}
      <div style={{ display:'flex', alignItems:'center', gap:8 }}>
        <div style={{
          width:24, height:24, borderRadius:5,
          background:`${ft.color}14`, border:`1px solid ${ft.color}28`,
          display:'flex', alignItems:'center', justifyContent:'center', shrink:0,
        }}>
          <FIcon size={11} color={ft.color} />
        </div>
        <div>
          <p style={{ fontFamily: T.sans, fontSize:12, color:T.t1, fontWeight:500 }}
             title={file.name}>{file.name?.length > 44 ? file.name.slice(0,44)+'ΓÇª' : file.name}</p>
          <p style={{ fontFamily: T.mono, fontSize:9, color:T.t3 }}>{file.file_key}</p>
        </div>
      </div>
      {/* Type */}
      <Pill label={ft.label} color={ft.color} />
      {/* Size */}
      <span style={{ fontFamily:T.mono, fontSize:11, color:T.t3 }}>{fmtBytes(file.size_bytes)}</span>
      {/* Age */}
      <span style={{ fontFamily:T.mono, fontSize:11, color:T.t3 }}>{fmtAge(file.last_modified)}</span>
      {/* Download */}
      <button
        onClick={download} disabled={loading}
        title="Get presigned download URL"
        style={{ background:'none', border:'none', cursor:'pointer', padding:4, opacity:0.5 }}
        onMouseEnter={e => e.currentTarget.style.opacity='1'}
        onMouseLeave={e => e.currentTarget.style.opacity='0.5'}
      >
        {loading ? <Loader2 size={12} color={T.gold} style={{animation:'spin 1s linear infinite'}} />
                 : <Download size={12} color={T.gold} />}
      </button>
    </div>
  )
}

/* ΓöÇΓöÇ Company card ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */
function CompanyCard({ company, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  const hasChunks = company.chunks_indexed > 0

  const ragColor = hasChunks ? T.green : company.has_data ? T.gold : T.t3
  const ragLabel = hasChunks ? `${company.chunks_indexed} chunks`
                 : company.has_data ? 'Data Γ£ô'
                 : 'PDF only'

  return (
    <div style={{
      background: T.panel,
      border: `1px solid ${open ? T.blue + '40' : T.border}`,
      borderRadius: 10, overflow:'hidden',
      transition: 'border-color 0.2s',
    }}>
      {/* Header */}
      <div
        onClick={() => setOpen(o => !o)}
        style={{
          display:'grid', gridTemplateColumns:'1fr auto auto auto auto',
          alignItems:'center', gap:14, padding:'14px 18px',
          cursor:'pointer', userSelect:'none',
          background: open ? T.panelH : 'transparent',
          transition:'background 0.15s',
        }}
      >
        {/* Ticker + name */}
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <div style={{
            width:34, height:34, borderRadius:8,
            background:`${T.blue}14`, border:`1px solid ${T.blue}25`,
            display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0,
          }}>
            <span style={{ fontFamily:T.mono, fontSize:10, fontWeight:700, color:T.blue }}>
              {company.ticker.slice(0,3)}
            </span>
          </div>
          <div>
            <p style={{ fontFamily:T.mono, fontSize:12, fontWeight:600, color:T.gold }}>{company.ticker}</p>
            <p style={{ fontFamily:T.sans, fontSize:11, color:T.t3 }}>{company.sector}</p>
          </div>
        </div>

        {/* PDF count */}
        <div style={{ textAlign:'center' }}>
          <p style={{ fontFamily:T.mono, fontSize:16, fontWeight:700, color:T.red }}>{company.pdf_count}</p>
          <p style={{ fontFamily:T.mono, fontSize:9, color:T.t3 }}>PDFs</p>
        </div>

        {/* Data files */}
        <div style={{ textAlign:'center' }}>
          <p style={{ fontFamily:T.mono, fontSize:16, fontWeight:700, color:T.green }}>{company.data_count}</p>
          <p style={{ fontFamily:T.mono, fontSize:9, color:T.t3 }}>Data</p>
        </div>

        {/* RAG status */}
        <div style={{ textAlign:'center', minWidth:80 }}>
          <p style={{ fontFamily:T.mono, fontSize:11, fontWeight:600, color:ragColor }}>{ragLabel}</p>
          <p style={{ fontFamily:T.mono, fontSize:9, color:T.t3 }}>RAG</p>
        </div>

        {/* Size + chevron */}
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <span style={{ fontFamily:T.mono, fontSize:10, color:T.t3 }}>{fmtBytes(company.total_bytes)}</span>
          {open
            ? <ChevronDown size={14} color={T.t2} />
            : <ChevronRight size={14} color={T.t3} />
          }
        </div>
      </div>

      {/* File list (expanded) */}
      {open && (
        <div style={{ borderTop:`1px solid ${T.divider}` }}>
          {/* Column headers */}
          <div style={{
            display:'grid', gridTemplateColumns:'1fr 72px 80px 60px 36px',
            padding:'7px 16px', background:'rgba(0,0,0,0.25)',
          }}>
            {['File','Type','Size','Uploaded',''].map(h => (
              <span key={h} style={{ fontFamily:T.mono, fontSize:9, color:T.t3, letterSpacing:'0.05em' }}>{h}</span>
            ))}
          </div>
          {company.files.length === 0
            ? <p style={{ fontFamily:T.mono, fontSize:11, color:T.t3, padding:'14px 18px' }}>No files found in S3</p>
            : company.files.map((f, i) => <FileRow key={f.file_key ?? i} file={f} />)
          }
        </div>
      )}
    </div>
  )
}

/* ΓöÇΓöÇ Main page ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */
export default function FilesPage() {
  const [data,      setData]      = useState(null)   // { companies, totals }
  const [loading,   setLoading]   = useState(false)
  const [error,     setError]     = useState(null)
  const [search,    setSearch]    = useState('')
  const [sector,    setSector]    = useState('ALL')
  const [sortBy,    setSortBy]    = useState('ticker')   // ticker | pdfs | chunks | size

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API}/uploads/sources?max_keys=2000`)
      if (!res.ok) throw new Error(`Server returned ${res.status}`)
      const json = await res.json()
      setData(json)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  /* ΓöÇΓöÇ Derived ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */
  const allCompanies = data?.companies ?? []

  const sectors = ['ALL', ...Array.from(new Set(
    allCompanies.map(c => c.sector).filter(Boolean)
  )).sort()]

  const filtered = allCompanies
    .filter(c => sector === 'ALL' || c.sector === sector)
    .filter(c => {
      if (!search) return true
      const q = search.toLowerCase()
      return c.ticker.toLowerCase().includes(q) || c.name.toLowerCase().includes(q)
    })
    .sort((a, b) => {
      if (sortBy === 'pdfs')   return b.pdf_count - a.pdf_count
      if (sortBy === 'chunks') return b.chunks_indexed - a.chunks_indexed
      if (sortBy === 'size')   return b.total_bytes - a.total_bytes
      return a.ticker.localeCompare(b.ticker)
    })

  return (
    <div style={{ flex:1, overflowY:'auto', background:T.bg, minHeight:'100vh' }}>
      <style>{`
        @keyframes sk { 0%,100%{opacity:0.3} 50%{opacity:0.7} }
        @keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
      `}</style>

      <div style={{ maxWidth:1100, margin:'0 auto', padding:'28px 24px 60px' }}>

        {/* ΓöÇΓöÇ Header ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */}
        <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom:24 }}>
          <div>
            <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:6 }}>
              <div style={{
                width:36, height:36, borderRadius:9,
                background:`${T.gold}18`, border:`1px solid ${T.gold}30`,
                display:'flex', alignItems:'center', justifyContent:'center',
              }}>
                <Database size={16} color={T.gold} />
              </div>
              <h1 style={{ fontFamily:T.mono, fontSize:22, fontWeight:700, color:T.t1, letterSpacing:'-0.02em' }}>
                Sources
              </h1>
              <span style={{
                fontFamily:T.mono, fontSize:9, letterSpacing:'0.06em',
                padding:'3px 8px', borderRadius:4,
                background:`${T.green}15`, color:T.green,
              }}>LIVE S3</span>
            </div>
            <p style={{ fontFamily:T.mono, fontSize:11, color:T.t3 }}>
              {loading ? 'Scanning S3 bucketΓÇª'
              : error  ? 'Could not load source data'
              : `${data?.totals?.companies ?? 0} companies ┬╖ ${data?.totals?.files ?? 0} files ┬╖ ${fmtBytes(data?.totals?.total_bytes)}`}
            </p>
          </div>

          <button
            onClick={load} disabled={loading}
            style={{
              display:'flex', alignItems:'center', gap:6,
              background:`${T.blue}12`, border:`1px solid ${T.blue}30`,
              borderRadius:8, padding:'8px 14px',
              fontFamily:T.mono, fontSize:11, color:T.blue,
              cursor:'pointer',
            }}
          >
            <RefreshCw size={13} style={loading ? {animation:'spin 1s linear infinite'} : {}} />
            Refresh
          </button>
        </div>

        {/* ΓöÇΓöÇ Stats bar ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */}
        <StatsBar totals={data?.totals} loading={loading} />

        {/* ΓöÇΓöÇ Filters ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */}
        <div style={{ display:'flex', gap:10, marginBottom:16, flexWrap:'wrap', alignItems:'center' }}>
          {/* Search */}
          <div style={{
            display:'flex', alignItems:'center', gap:8,
            background:T.panel, border:`1px solid ${T.border}`,
            borderRadius:8, padding:'7px 12px', flex:'0 0 220px',
          }}>
            <Search size={13} color={T.t3} />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search ticker or nameΓÇª"
              style={{
                background:'none', border:'none', outline:'none',
                fontFamily:T.mono, fontSize:11, color:T.t1, width:'100%',
              }}
            />
          </div>

          {/* Sector tabs */}
          <div style={{ display:'flex', gap:6, flexWrap:'wrap' }}>
            {sectors.map(s => (
              <button
                key={s}
                onClick={() => setSector(s)}
                style={{
                  fontFamily:T.mono, fontSize:10, letterSpacing:'0.04em',
                  padding:'5px 12px', borderRadius:6, cursor:'pointer',
                  background: sector===s ? `${T.blue}20` : 'transparent',
                  border: `1px solid ${sector===s ? T.blue+'60' : T.border}`,
                  color: sector===s ? T.blue : T.t3,
                  transition:'all 0.15s',
                }}
              >{s}</button>
            ))}
          </div>

          {/* Sort */}
          <div style={{ marginLeft:'auto', display:'flex', alignItems:'center', gap:6 }}>
            <Filter size={12} color={T.t3} />
            {[['ticker','AΓÇôZ'],['pdfs','PDFs'],['chunks','RAG'],['size','Size']].map(([k,l]) => (
              <button
                key={k}
                onClick={() => setSortBy(k)}
                style={{
                  fontFamily:T.mono, fontSize:10, padding:'5px 10px', borderRadius:6,
                  background: sortBy===k ? `${T.gold}18` : 'transparent',
                  border:`1px solid ${sortBy===k ? T.gold+'50':'transparent'}`,
                  color: sortBy===k ? T.gold : T.t3, cursor:'pointer',
                  transition:'all 0.15s',
                }}
              >{l}</button>
            ))}
          </div>
        </div>

        {/* ΓöÇΓöÇ Content ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */}
        {error ? (
          <div style={{
            textAlign:'center', padding:'60px 0',
            background:T.panel, borderRadius:12, border:`1px solid ${T.border}`,
          }}>
            <AlertCircle size={32} color={T.red} style={{ margin:'0 auto 14px' }} />
            <p style={{ fontFamily:T.sans, fontSize:14, color:T.t1, marginBottom:6 }}>Could not load sources</p>
            <p style={{ fontFamily:T.mono, fontSize:11, color:T.t3, marginBottom:16 }}>{error}</p>
            <button onClick={load} style={{
              fontFamily:T.mono, fontSize:11, color:T.blue,
              background:'none', border:'none', cursor:'pointer', textDecoration:'underline',
            }}>Retry</button>
          </div>
        ) : loading ? (
          <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
            {Array.from({length:6}).map((_,i) => (
              <div key={i} style={{
                height:60, borderRadius:10,
                background:T.panel, border:`1px solid ${T.border}`,
                animation:'sk 1.6s ease infinite',
              }} />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ textAlign:'center', padding:'60px 0' }}>
            <FileText size={32} color={T.t3} style={{ margin:'0 auto 14px', opacity:0.3 }} />
            <p style={{ fontFamily:T.sans, fontSize:13, color:T.t2 }}>No companies match your filter</p>
          </div>
        ) : (
          <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
            {filtered.map((company, i) => (
              <CompanyCard
                key={company.ticker}
                company={company}
                defaultOpen={i < 3 && filtered.length <= 5}
              />
            ))}
          </div>
        )}

        {/* Footer */}
        {!loading && !error && data && (
          <p style={{
            fontFamily:T.mono, fontSize:10, color:T.t3,
            textAlign:'center', marginTop:28,
          }}>
            {filtered.length} of {allCompanies.length} companies shown
            ┬╖ Presigned download URLs expire in 1 hour
            ┬╖ Source: AWS S3 + Aurora pgvector
          </p>
        )}
      </div>
    </div>
  )
}
