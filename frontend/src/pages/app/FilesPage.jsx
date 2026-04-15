// src/pages/app/FilesPage.jsx — EREBUS Sources Visualization
// Powered by GET /uploads/sources (live S3 + pgvector)

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Database, FileText, BarChart2, Search, RefreshCw,
  ChevronDown, ChevronRight, Download, Loader2,
  AlertCircle, CheckCircle, Layers, Filter,
  File, FileSpreadsheet, Code2, Image as ImageIcon,
  ExternalLink, Box, Eye, Trash2, Clock, FileImage,
} from 'lucide-react'
import FileViewer from '../../components/ui/FileViewer'
import FileUploader from '../../components/ui/FileUploader'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

/* ── Status config ──────────────────────────────────────────────────────── */
const STATUS_META = {
  indexed: { icon: CheckCircle, cls: 'text-erebus-green', label: 'Indexed' },
  processing: { icon: Clock, cls: 'text-erebus-amber', label: 'Processing' },
  failed: { icon: AlertCircle, cls: 'text-erebus-red', label: 'Failed' },
}

/* ── File type helpers ──────────────────────────────────────────────────── */
function getExt(name = '') { return name.split('.').pop().toLowerCase() }

function FileTypeIcon({ name }) {
  const ext = getExt(name)
  if (ext === 'pdf') return <FileText size={12} className="text-erebus-red" />
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'].includes(ext))
    return <FileImage size={12} className="text-erebus-blue" />
  if (['csv', 'xlsx', 'xls', 'xlsm'].includes(ext))
    return <FileSpreadsheet size={12} className="text-erebus-green" />
  return <FileText size={12} className="text-erebus-blue" />
}

function getViewerLabel(name = '') {
  const ext = getExt(name)
  if (ext === 'pdf') return 'Preview PDF'
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'].includes(ext)) return 'View image'
  if (['csv', 'xlsx', 'xls'].includes(ext)) return 'Open spreadsheet'
  return 'Open file'

}
/* ── Design tokens ──────────────────────────────────────────────────────────── */
const T = {
  bg: '#07090E',
  panel: '#0F1420',
  panelH: '#141929',
  border: 'rgba(255,255,255,0.07)',
  divider: 'rgba(255,255,255,0.045)',
  blue: '#4A8FE7',
  green: '#22C55E',
  gold: '#C9A84C',
  red: '#E7534A',
  t1: '#E8ECF4',
  t2: '#8B93A8',
  t3: '#4A5166',
  mono: "'JetBrains Mono', monospace",
  sans: "'Inter', sans-serif",
}

/* ── File type config ────────────────────────────────────────────────────────── */
const FTYPE = {
  PDF: { color: T.red, Icon: FileText, label: 'PDF' },
  EXCEL: { color: T.green, Icon: FileSpreadsheet, label: 'XLSX' },
  CSV: { color: T.green, Icon: BarChart2, label: 'CSV' },
  JSON: { color: T.blue, Icon: Code2, label: 'JSON' },
  TXT: { color: T.t2, Icon: FileText, label: 'TXT' },
  IMAGE: { color: T.gold, Icon: ImageIcon, label: 'IMG' },
  OTHER: { color: T.t3, Icon: File, label: 'FILE' },
}

/* ── Formatters ──────────────────────────────────────────────────────────────── */
function fmtBytes(b) {
  if (!b) return '—'
  if (b < 1024) return `${b} B`
  if (b < 1048576) return `${(b / 1024).toFixed(1)} KB`
  if (b < 1073741824) return `${(b / 1048576).toFixed(1)} MB`
  return `${(b / 1073741824).toFixed(2)} GB`
}

function fmtAge(iso) {
  if (!iso) return '—'
  try {
    const d = Date.now() - new Date(iso).getTime()
    const m = Math.floor(d / 60000)
    if (m < 2) return 'Just now'
    if (m < 60) return `${m}m ago`
    const h = Math.floor(m / 60)
    if (h < 24) return `${h}h ago`
    const dy = Math.floor(h / 24)
    if (dy < 7) return `${dy}d ago`
    return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
  } catch { return '—' }
}
function formatDate(iso) {
  try {
    const d = new Date(iso)
    const diff = Date.now() - d.getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 2) return 'Just now'
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h ago`
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
  } catch { return iso }
}

/* ── Pill badge ──────────────────────────────────────────────────────────────── */
function Pill({ label, color, bg }) {
  return (
    <span style={{
      fontFamily: T.mono, fontSize: 9, letterSpacing: '0.06em',
      padding: '2px 6px', borderRadius: 3,
      background: bg ?? `${color}18`, color,
    }}>{label}</span>
  )
}

/* ── Stats bar ───────────────────────────────────────────────────────────────── */
function StatsBar({ totals, loading }) {
  const stats = [
    { label: 'Companies', value: totals?.companies ?? 0, color: T.blue, Icon: Box },
    { label: 'Research PDFs', value: totals?.pdfs ?? 0, color: T.red, Icon: FileText },
    { label: 'Total Files', value: totals?.files ?? 0, color: T.gold, Icon: Database },
    { label: 'Chunks in RAG', value: totals?.chunks ?? 0, color: T.green, Icon: Layers },
    { label: 'Storage', value: fmtBytes(totals?.total_bytes), color: T.t2, Icon: BarChart2 },
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
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
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

/* ── File row inside expanded company ────────────────────────────────────────── */
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
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{
          width: 24, height: 24, borderRadius: 5,
          background: `${ft.color}14`, border: `1px solid ${ft.color}28`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', shrink: 0,
        }}>
          <FIcon size={11} color={ft.color} />
        </div>
        <div>
          <p style={{ fontFamily: T.sans, fontSize: 12, color: T.t1, fontWeight: 500 }}
            title={file.name}>{file.name?.length > 44 ? file.name.slice(0, 44) + '…' : file.name}</p>
          <p style={{ fontFamily: T.mono, fontSize: 9, color: T.t3 }}>{file.file_key}</p>
        </div>
      </div>
      {/* Type */}
      <Pill label={ft.label} color={ft.color} />
      {/* Size */}
      <span style={{ fontFamily: T.mono, fontSize: 11, color: T.t3 }}>{fmtBytes(file.size_bytes)}</span>
      {/* Age */}
      <span style={{ fontFamily: T.mono, fontSize: 11, color: T.t3 }}>{fmtAge(file.last_modified)}</span>
      {/* Download */}
      <button
        onClick={download} disabled={loading}
        title="Get presigned download URL"
        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4, opacity: 0.5 }}
        onMouseEnter={e => e.currentTarget.style.opacity = '1'}
        onMouseLeave={e => e.currentTarget.style.opacity = '0.5'}
      >
        {loading ? <Loader2 size={12} color={T.gold} style={{ animation: 'spin 1s linear infinite' }} />
          : <Download size={12} color={T.gold} />}
      </button>
    </div>
  )
}

/* ── S3 File row (Table row format) ─────────────────────────────────────────── */
function S3FileRow({ file, onDelete, onOpen }) {
  const [deleting, setDeleting]  = useState(false)
  const [opening,  setOpening]   = useState(false)

  const name   = file.name ?? file.file_key?.split('/').pop() ?? '—'
  const status = file.status ?? 'indexed'
  const sm     = STATUS_META[status] ?? STATUS_META.indexed
  const Icon   = sm.icon

  return (
    <tr className="border-t border-white/[0.05] group hover:bg-erebus-surface-2 transition-colors">
      <td className="px-5 py-3.5">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-erebus-surface border border-white/[0.08] flex items-center justify-center shrink-0">
            <FileTypeIcon name={name} />
          </div>
          <div className="min-w-0">
            <p className="text-[13px] font-medium text-erebus-text-1 truncate max-w-[240px]">{name}</p>
            <p className="text-[10px] font-mono text-erebus-text-3 truncate max-w-[240px]">{file.file_key}</p>
          </div>
        </div>
      </td>
      <td className="px-5 py-3.5 font-mono text-[12px] text-erebus-text-3">{file.size ?? fmtBytes(file.size_bytes)}</td>
      <td className="px-5 py-3.5 font-mono text-[12px] text-erebus-text-3">{file.date ?? fmtAge(file.last_modified)}</td>
      <td className="px-5 py-3.5">
        <div className="flex items-center gap-1.5">
          <Icon size={12} className={sm.cls} />
          <span className={`text-[11px] font-mono ${sm.cls}`}>{sm.label}</span>
        </div>
      </td>
      <td className="px-5 py-3.5">
        <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <button onClick={() => { setOpening(true); onOpen(file.file_key, name).finally(()=>setOpening(false)) }} disabled={opening} title={getViewerLabel(name)} className="flex items-center gap-1 px-2 py-1 rounded text-[11px] font-mono text-erebus-text-3 hover:text-erebus-gold hover:bg-erebus-gold/[0.08] transition-colors disabled:opacity-40">
            {opening ? <Loader2 size={12} className="animate-spin" /> : <Eye size={12} />}<span>Open</span>
          </button>
          <button onClick={() => { if(window.confirm(`Delete ${name}?`)) { setDeleting(true); onDelete(file.file_key).finally(()=>setDeleting(false)) } }} disabled={deleting} title="Delete file" className="p-1 rounded text-erebus-text-3 hover:text-erebus-red transition-colors disabled:opacity-40">
            {deleting ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
          </button>
        </div>
      </td>
    </tr>
  )
}

/* ── Company card ────────────────────────────────────────────────────────────── */
function CompanyCard({ company, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  const hasChunks = company.chunks_indexed > 0

  const ragColor = hasChunks ? T.green : company.has_data ? T.gold : T.t3
  const ragLabel = hasChunks ? `${company.chunks_indexed} chunks`
    : company.has_data ? 'Data ✓'
      : 'PDF only'

  return (
    <div style={{
      background: T.panel,
      border: `1px solid ${open ? T.blue + '40' : T.border}`,
      borderRadius: 10, overflow: 'hidden',
      transition: 'border-color 0.2s',
    }}>
      {/* Header */}
      <div
        onClick={() => setOpen(o => !o)}
        style={{
          display: 'grid', gridTemplateColumns: '1fr auto auto auto auto',
          alignItems: 'center', gap: 14, padding: '14px 18px',
          cursor: 'pointer', userSelect: 'none',
          background: open ? T.panelH : 'transparent',
          transition: 'background 0.15s',
        }}
      >
        {/* Ticker + name */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 34, height: 34, borderRadius: 8,
            background: `${T.blue}14`, border: `1px solid ${T.blue}25`,
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <span style={{ fontFamily: T.mono, fontSize: 10, fontWeight: 700, color: T.blue }}>
              {company.ticker.slice(0, 3)}
            </span>
          </div>
          <div className="min-w-0">
            <p className="text-[13px] font-medium text-erebus-text-1 truncate max-w-[240px]">
              {name}
            </p>
            <p className="text-[10px] font-mono text-erebus-text-3 truncate max-w-[240px]">
              {file.file_key}
            </p>
          </div>
        </div>

        {/* PDF count */}
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontFamily: T.mono, fontSize: 16, fontWeight: 700, color: T.red }}>{company.pdf_count}</p>
          <p style={{ fontFamily: T.mono, fontSize: 9, color: T.t3 }}>PDFs</p>
        </div>

        {/* Data files */}
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontFamily: T.mono, fontSize: 16, fontWeight: 700, color: T.green }}>{company.data_count}</p>
          <p style={{ fontFamily: T.mono, fontSize: 9, color: T.t3 }}>Data</p>
        </div>

        {/* RAG status */}
        <div style={{ textAlign: 'center', minWidth: 80 }}>
          <p style={{ fontFamily: T.mono, fontSize: 11, fontWeight: 600, color: ragColor }}>{ragLabel}</p>
          <p style={{ fontFamily: T.mono, fontSize: 9, color: T.t3 }}>RAG</p>
        </div>

        {/* Size + chevron */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontFamily: T.mono, fontSize: 10, color: T.t3 }}>{fmtBytes(company.total_bytes)}</span>
          {open
            ? <ChevronDown size={14} color={T.t2} />
            : <ChevronRight size={14} color={T.t3} />
          }
        </div>
      </div>

      {/* File list (expanded) */}
      {open && (
        <div style={{ borderTop: `1px solid ${T.divider}` }}>
          {/* Column headers */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 72px 80px 60px 36px',
            padding: '7px 16px', background: 'rgba(0,0,0,0.25)',
          }}>
            {['File', 'Type', 'Size', 'Uploaded', ''].map(h => (
              <span key={h} style={{ fontFamily: T.mono, fontSize: 9, color: T.t3, letterSpacing: '0.05em' }}>{h}</span>
            ))}
          </div>
          {company.files.length === 0
            ? <p style={{ fontFamily: T.mono, fontSize: 11, color: T.t3, padding: '14px 18px' }}>No files found in S3</p>
            : company.files.map((f, i) => <FileRow key={f.file_key ?? i} file={f} />)
          }
        </div>
      )}
    </div>
  )
}

/* ── Main page ───────────────────────────────────────────────────────────────── */
export default function FilesPage() {
  const [s3Files, setS3Files] = useState([])
  const [s3Loading, setS3Loading] = useState(false)
  const [s3Error, setS3Error] = useState(null)
  const [uploadCount, setUploadCount] = useState(0)
  const [data, setData] = useState(null)   // { companies, totals }
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [sector, setSector] = useState('ALL')
  const [sortBy, setSortBy] = useState('ticker')   // ticker | pdfs | chunks | size

  // Viewer state
  const [viewerUrl, setViewerUrl] = useState(null)
  const [viewerName, setViewerName] = useState('')

  /* Load S3 file list — both uploads/ and ocr-uploads/ folders */
  const fetchFiles = useCallback(async () => {
    setS3Loading(true)
    setS3Error(null)
    try {
      const [r1, r2] = await Promise.all([
        fetch(`${API}/uploads/files?prefix=uploads&max_keys=200`),
        fetch(`${API}/uploads/files?prefix=ocr-uploads&max_keys=200`),
      ])
      const [d1, d2] = await Promise.all([r1.json(), r2.json()])
      const merged = [...(d1.files ?? []), ...(d2.files ?? [])]
      merged.sort((a, b) => new Date(b.last_modified) - new Date(a.last_modified))
      setS3Files(merged)
    } catch (err) {
      setS3Error(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchFiles() }, [fetchFiles])

  /* Delete */
  const handleDelete = useCallback(async (fileKey) => {
    try {
      const res = await fetch(`${API}/uploads/file`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_key: fileKey }),
      })
      if (!res.ok) throw new Error(`Delete failed: ${res.status}`)
      setS3Files(prev => prev.filter(f => f.file_key !== fileKey))
    } catch (err) {
      alert(`Could not delete file: ${err.message}`)
    }
  }, [])

  /* Open — get presigned URL then show viewer */
  const handleOpen = useCallback(async (fileKey, fileName) => {
    try {
      const res = await fetch(`${API}/uploads/generate-download-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_key: fileKey }),
      })
      if (!res.ok) throw new Error(`Could not get URL: ${res.status}`)
      const { download_url } = await res.json()
      setViewerName(fileName)
      setViewerUrl(download_url)
    } catch (err) {
      alert(err.message)
    }
  }, [])

  const handleUploadSuccess = useCallback(() => {
    setUploadCount(n => n + 1)
  }, [])

  return (
    <div style={{ flex: 1, overflowY: 'auto', background: T.bg, minHeight: '100vh' }}>
      <style>{`
        @keyframes sk { 0%,100%{opacity:0.3} 50%{opacity:0.7} }
        @keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
      `}</style>

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '28px 24px 60px' }}>

        {/* ── Header ─────────────────────────────────────────────────────────── */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
              <div style={{
                width: 36, height: 36, borderRadius: 9,
                background: `${T.gold}18`, border: `1px solid ${T.gold}30`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Database size={16} color={T.gold} />
              </div>
              <h1 style={{ fontFamily: T.mono, fontSize: 22, fontWeight: 700, color: T.t1, letterSpacing: '-0.02em' }}>
                Sources
              </h1>
              <span style={{
                fontFamily: T.mono, fontSize: 9, letterSpacing: '0.06em',
                padding: '3px 8px', borderRadius: 4,
                background: `${T.green}15`, color: T.green,
              }}>LIVE S3</span>
            </div>
            <p className="text-[12px] font-mono text-erebus-text-3">
              {s3Loading
                ? 'Loading…'
                : s3Error
                  ? 'Could not load file list'
                  : `${s3Files.length} documents in S3`
              }
            </p>
          </div>

          <button
            onClick={fetchFiles} disabled={loading}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              background: `${T.blue}12`, border: `1px solid ${T.blue}30`,
              borderRadius: 8, padding: '8px 14px',
              fontFamily: T.mono, fontSize: 11, color: T.blue,
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={13} style={loading ? { animation: 'spin 1s linear infinite' } : {}} />
            Refresh
          </button>
        </div>

        {/* Upload zone */}
        <div className="mb-6">
          <FileUploader
            prefix="uploads"
            onSuccess={handleUploadSuccess}
            label="Drop documents here, or click to browse"
          />
        </div>

        {/* File table */}
        <div className="elevated rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-erebus-surface border-b border-white/[0.07]">
                {['Document', 'Size', 'Uploaded', 'Status', ''].map(h => (
                  <th key={h} className="px-5 py-3.5 text-left text-[10px] font-mono text-erebus-text-3 uppercase tracking-wider">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {s3Loading && s3Files.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-5 py-12 text-center">
                    <Loader2 size={20} className="mx-auto mb-2 animate-spin text-erebus-text-3" />
                    <p className="text-[12px] font-mono text-erebus-text-3">Loading from S3…</p>
                  </td>
                </tr>
              ) : s3Error ? (
                <tr>
                  <td colSpan={5} className="px-5 py-12 text-center">
                    <AlertCircle size={20} className="mx-auto mb-2 text-erebus-red" />
                    <p className="text-[13px] text-erebus-text-2 mb-1">Could not load files</p>
                    <p className="text-[11px] font-mono text-erebus-text-3">{s3Error}</p>
                    <button onClick={fetchFiles} className="mt-3 text-[11px] font-mono text-erebus-gold hover:underline">
                      Retry
                    </button>
                  </td>
                </tr>
              ) : s3Files.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-5 py-12 text-center">
                    <FileText size={24} className="mx-auto mb-3 text-erebus-text-3 opacity-40" />
                    <p className="text-[13px] font-medium text-erebus-text-2 mb-1">No files uploaded yet</p>
                    <p className="text-[11px] font-mono text-erebus-text-3">
                      Drop a file above to upload directly to S3
                    </p>
                  </td>
                </tr>
              ) : (
                s3Files.map((file, i) => (
                  <S3FileRow
                    key={file.file_key ?? i}
                    file={file}
                    onDelete={handleDelete}
                    onOpen={handleOpen}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>

        {s3Files.length > 0 && (
          <p className="mt-3 text-[11px] font-mono text-erebus-text-3 text-right">
            Files stored in S3 · Download links expire in 1 hour
          </p>
        )}
      </div>

      {/* File viewer modal */}
      <FileViewer
        url={viewerUrl}
        fileName={viewerName}
        onClose={() => { setViewerUrl(null); setViewerName('') }}
      />
    </div>
  )
}
