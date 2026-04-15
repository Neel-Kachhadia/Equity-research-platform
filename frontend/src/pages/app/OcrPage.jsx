// src/pages/app/OcrPage.jsx
import { useState, useCallback, useEffect, useRef } from 'react'
import {
  ScanText, Loader2, CheckCircle, AlertCircle, Clock,
  Upload, Copy, Download, Eye, RefreshCw,
  FileText, ChevronRight, Zap, Brain,
  Building2, User, Calendar, DollarSign, Tag, Flag,
  TrendingUp, TrendingDown, Minus,
} from 'lucide-react'
import FileUploader from '../../components/ui/FileUploader'
import FileViewer   from '../../components/ui/FileViewer'
import {
  registerDocument,
  processDocument,
  getDocument,
  getResult,
  listHistory,
  analyzeDocument,
} from '../../services/ocrService'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const POLL_INTERVAL_MS = 3000

/* ── Helpers ─────────────────────────────────────────────────────────────── */
function formatBytes(bytes) {
  if (!bytes) return '—'
  const k = 1024, sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}

function formatDate(iso) {
  if (!iso) return '—'
  try {
    const d    = new Date(iso)
    const diff = Date.now() - d.getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 2)  return 'Just now'
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24)  return `${hrs}h ago`
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
  } catch { return iso }
}

async function getPresignedUrl(fileKey) {
  const res = await fetch(`${API_BASE}/uploads/generate-download-url`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ file_key: fileKey }),
  })
  if (!res.ok) throw new Error(`Could not get URL: ${res.status}`)
  const { download_url } = await res.json()
  return download_url
}

/* ── Status config ───────────────────────────────────────────────────────── */
const STATUS = {
  uploaded:   { label: 'Uploaded',   icon: Clock,       cls: 'text-erebus-text-3', bg: 'bg-white/[0.06]' },
  processing: { label: 'Processing', icon: Loader2,     cls: 'text-erebus-amber',  bg: 'bg-erebus-amber/[0.08]', spin: true },
  completed:  { label: 'Completed',  icon: CheckCircle, cls: 'text-erebus-green',  bg: 'bg-erebus-green/[0.08]' },
  failed:     { label: 'Failed',     icon: AlertCircle, cls: 'text-erebus-red',    bg: 'bg-erebus-red/[0.08]' },
}

function StatusBadge({ status }) {
  const s    = STATUS[status] ?? STATUS.uploaded
  const Icon = s.icon
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono ${s.cls} ${s.bg}`}>
      <Icon size={11} className={s.spin ? 'animate-spin' : ''} />
      {s.label}
    </span>
  )
}

/* ── Document Info Card ──────────────────────────────────────────────────── */
function DocumentCard({ doc, onRunOcr, running, onView }) {
  const [viewLoading, setViewLoading] = useState(false)
  const canRun = doc.status === 'uploaded' || doc.status === 'failed'

  async function handleView() {
    if (!doc.s3_key) return
    setViewLoading(true)
    try {
      const url = await getPresignedUrl(doc.s3_key)
      onView(url, doc.file_name)
    } catch (e) {
      alert(e.message)
    } finally {
      setViewLoading(false)
    }
  }

  return (
    <div className="elevated rounded-xl p-5 border border-white/[0.06]">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 rounded-lg bg-erebus-blue/[0.10] border border-erebus-blue/20 flex items-center justify-center shrink-0">
            <FileText size={18} className="text-erebus-blue" />
          </div>
          <div className="min-w-0">
            <button
              onClick={handleView}
              disabled={viewLoading || !doc.s3_key}
              className="text-[14px] font-medium text-erebus-text-1 truncate max-w-[320px] hover:text-erebus-gold transition-colors text-left disabled:opacity-40"
            >
              {viewLoading
                ? <span className="flex items-center gap-1.5"><Loader2 size={12} className="animate-spin" />{doc.file_name}</span>
                : doc.file_name
              }
            </button>
            <p className="text-[12px] font-mono text-erebus-text-3 mt-0.5">
              {doc.mime_type} · {formatBytes(doc.file_size)} · Uploaded {formatDate(doc.upload_created_at)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {doc.s3_key && (
            <button
              onClick={handleView}
              disabled={viewLoading}
              title="Preview file"
              className="flex items-center gap-1 px-2 py-1 rounded text-[11px] font-mono text-erebus-text-3 hover:text-erebus-gold hover:bg-erebus-gold/[0.08] transition-colors disabled:opacity-40"
            >
              {viewLoading ? <Loader2 size={11} className="animate-spin" /> : <Eye size={11} />}
              Preview
            </button>
          )}
          <StatusBadge status={doc.status} />
        </div>
      </div>

      {doc.error_message && (
        <div className="mt-4 rounded-lg bg-erebus-red/[0.06] border border-erebus-red/20 px-4 py-3">
          <p className="text-[12px] font-mono text-erebus-red">{doc.error_message}</p>
        </div>
      )}

      {canRun && (
        <button
          id="ocr-run-button"
          onClick={onRunOcr}
          disabled={running}
          className="mt-4 flex items-center gap-2 px-4 py-2 rounded-lg bg-erebus-gold/[0.12] border border-erebus-gold/30 text-erebus-gold text-[13px] font-medium hover:bg-erebus-gold/[0.20] transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {running
            ? <><Loader2 size={14} className="animate-spin" /> Starting OCR…</>
            : <><Zap size={14} /> Run OCR</>
          }
        </button>
      )}

      {doc.status === 'processing' && (
        <div className="mt-4 flex items-center gap-3">
          <div className="flex-1 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
            <div className="h-full w-1/3 rounded-full bg-erebus-amber animate-pulse" />
          </div>
          <span className="text-[11px] font-mono text-erebus-text-3">Processing…</span>
        </div>
      )}
    </div>
  )
}

/* ── OCR Result Viewer ───────────────────────────────────────────────────── */
function ResultViewer({ result, doc }) {
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    navigator.clipboard?.writeText(result.extracted_text ?? '').catch(() => {})
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  function handleDownload() {
    const blob = new Blob([result.extracted_text ?? ''], { type: 'text/plain' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `${doc.file_name.replace(/\.[^.]+$/, '')}_ocr.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const hasPages = result.pages?.length > 1

  return (
    <div className="elevated rounded-xl overflow-hidden border border-erebus-green/[0.12]">
      <div className="flex items-center justify-between px-5 py-3.5 bg-erebus-surface border-b border-white/[0.07]">
        <div className="flex items-center gap-2">
          <CheckCircle size={14} className="text-erebus-green" />
          <span className="text-[13px] font-medium text-erebus-text-1">Extracted Text</span>
          {result.page_count > 1 && (
            <span className="ml-1 text-[11px] font-mono text-erebus-text-3">{result.page_count} pages</span>
          )}
          {result.confidence_avg != null && (
            <span className="text-[11px] font-mono text-erebus-text-3">· {result.confidence_avg}% confidence</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            id="ocr-copy-button"
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-mono text-erebus-text-3 hover:text-erebus-gold hover:bg-erebus-gold/[0.08] transition-all"
          >
            <Copy size={11} />
            {copied ? 'Copied!' : 'Copy'}
          </button>
          <button
            id="ocr-download-button"
            onClick={handleDownload}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-mono text-erebus-text-3 hover:text-erebus-blue hover:bg-erebus-blue/[0.08] transition-all"
          >
            <Download size={11} />
            Download .txt
          </button>
        </div>
      </div>

      {!result.extracted_text ? (
        <div className="px-5 py-10 text-center">
          <AlertCircle size={20} className="mx-auto mb-2 text-erebus-text-3 opacity-40" />
          <p className="text-[13px] text-erebus-text-3">No text was extracted from this document.</p>
        </div>
      ) : hasPages ? (
        <div className="divide-y divide-white/[0.05]">
          {result.pages.map(pg => (
            <details key={pg.page_number} className="group">
              <summary className="flex items-center gap-2 px-5 py-3 cursor-pointer list-none hover:bg-erebus-surface-2 transition-colors">
                <ChevronRight size={12} className="text-erebus-text-3 group-open:rotate-90 transition-transform shrink-0" />
                <span className="text-[12px] font-mono text-erebus-text-2">Page {pg.page_number}</span>
                <span className="text-[11px] font-mono text-erebus-text-3 ml-auto">
                  {pg.page_text?.split('\n').length ?? 0} lines
                </span>
              </summary>
              <pre className="px-5 pb-5 pt-2 text-[12px] font-mono text-erebus-text-2 leading-relaxed whitespace-pre-wrap break-words bg-erebus-bg/40">
                {pg.page_text}
              </pre>
            </details>
          ))}
        </div>
      ) : (
        <pre
          id="ocr-result-text"
          className="px-5 py-5 text-[12px] font-mono text-erebus-text-2 leading-relaxed whitespace-pre-wrap break-words max-h-[480px] overflow-y-auto scrollbar-none bg-erebus-bg/40"
        >
          {result.extracted_text}
        </pre>
      )}
    </div>
  )
}

/* ── AI Analysis Panel ───────────────────────────────────────────────────── */

const SENTIMENT_CONFIG = {
  positive: { Icon: TrendingUp,   color: 'text-erebus-green', bg: 'bg-erebus-green/[0.10]', border: 'border-erebus-green/20' },
  negative: { Icon: TrendingDown, color: 'text-erebus-red',   bg: 'bg-erebus-red/[0.10]',   border: 'border-erebus-red/20'   },
  neutral:  { Icon: Minus,        color: 'text-erebus-text-3',bg: 'bg-white/[0.05]',         border: 'border-white/10'        },
  mixed:    { Icon: Minus,        color: 'text-erebus-amber', bg: 'bg-erebus-amber/[0.10]',  border: 'border-erebus-amber/20' },
}

function EntityChip({ text }) {
  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-mono bg-white/[0.06] text-erebus-text-2 border border-white/[0.08]">
      {text}
    </span>
  )
}

function AnalysisPanel({ data, onDismiss }) {
  const { analysis, provider } = data
  const sentiment = SENTIMENT_CONFIG[analysis.sentiment?.label] ?? SENTIMENT_CONFIG.neutral
  const SentIcon  = sentiment.Icon

  return (
    <div className="rounded-xl overflow-hidden border border-erebus-gold/[0.18] bg-erebus-surface">

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-white/[0.07] bg-erebus-gold/[0.04]">
        <div className="flex items-center gap-2">
          <Brain size={15} className="text-erebus-gold" />
          <span className="text-[13px] font-semibold text-erebus-text-1">AI Analysis</span>
          <span className="text-[10px] font-mono text-erebus-text-3 bg-white/[0.06] px-2 py-0.5 rounded-full uppercase tracking-wider">
            via {provider}
          </span>
          {analysis.document_type && (
            <span className="text-[10px] font-mono text-erebus-gold bg-erebus-gold/[0.08] border border-erebus-gold/20 px-2 py-0.5 rounded-full">
              {analysis.document_type}
            </span>
          )}
        </div>
        <button
          onClick={onDismiss}
          className="text-[11px] font-mono text-erebus-text-3 hover:text-erebus-text-2 transition-colors"
        >
          Dismiss
        </button>
      </div>

      <div className="p-5 space-y-5">

        {/* Executive Summary */}
        <div>
          <p className="text-[10px] font-mono text-erebus-text-3 uppercase tracking-wider mb-2">Executive Summary</p>
          <p className="text-[14px] text-erebus-text-1 leading-relaxed">{analysis.summary}</p>
        </div>

        {/* Sentiment + Confidence row */}
        <div className="flex items-stretch gap-3">
          <div className={`flex-1 flex items-center gap-3 px-4 py-3 rounded-lg ${sentiment.bg} border ${sentiment.border}`}>
            <SentIcon size={18} className={sentiment.color} />
            <div>
              <p className={`text-[13px] font-semibold capitalize ${sentiment.color}`}>
                {analysis.sentiment?.label ?? 'unknown'}
              </p>
              <p className="text-[12px] text-erebus-text-3 mt-0.5">{analysis.sentiment?.reasoning}</p>
            </div>
          </div>
          {analysis.confidence && (
            <div className="flex flex-col items-center justify-center px-5 py-3 rounded-lg bg-white/[0.04] border border-white/[0.08]">
              <p className="text-[10px] font-mono text-erebus-text-3 uppercase tracking-wider mb-1">OCR Quality</p>
              <p className={`text-[14px] font-bold capitalize font-mono ${
                analysis.confidence === 'high' ? 'text-erebus-green' :
                analysis.confidence === 'medium' ? 'text-erebus-amber' : 'text-erebus-red'
              }`}>{analysis.confidence}</p>
            </div>
          )}
        </div>

        {/* Key Topics */}
        {analysis.key_topics?.length > 0 && (
          <div>
            <p className="text-[10px] font-mono text-erebus-text-3 uppercase tracking-wider mb-2">Key Topics</p>
            <div className="flex flex-wrap gap-2">
              {analysis.key_topics.map((t, i) => (
                <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[12px] font-mono bg-erebus-blue/[0.10] border border-erebus-blue/20 text-erebus-blue">
                  <Tag size={10} /> {t}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Entities */}
        {analysis.key_entities && (
          <div className="grid grid-cols-2 gap-3">
            {[
              { key: 'companies',         label: 'Companies',          Icon: Building2 },
              { key: 'people',            label: 'People',             Icon: User      },
              { key: 'dates',             label: 'Dates & Periods',    Icon: Calendar  },
              { key: 'financial_figures', label: 'Financial Figures',  Icon: DollarSign},
            ].map(({ key, label, Icon: EIcon }) => {
              const items = analysis.key_entities[key] ?? []
              if (!items.length) return null
              return (
                <div key={key} className="rounded-lg bg-white/[0.03] border border-white/[0.07] p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <EIcon size={12} className="text-erebus-text-3" />
                    <p className="text-[10px] font-mono text-erebus-text-3 uppercase tracking-wider">{label}</p>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {items.map((item, i) => <EntityChip key={i} text={item} />)}
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Action Items / Red Flags */}
        {analysis.action_items?.length > 0 && (
          <div className="rounded-lg bg-erebus-red/[0.05] border border-erebus-red/[0.15] p-4">
            <div className="flex items-center gap-2 mb-3">
              <Flag size={13} className="text-erebus-red" />
              <p className="text-[12px] font-mono text-erebus-red uppercase tracking-wider">Action Items & Red Flags</p>
            </div>
            <ul className="space-y-2">
              {analysis.action_items.map((item, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-erebus-red mt-1.5 shrink-0" />
                  <p className="text-[13px] text-erebus-text-2">{item}</p>
                </li>
              ))}
            </ul>
          </div>
        )}

      </div>
    </div>
  )
}

/* ── History Table ────────────────────────────────────────────────────────── */
function HistoryTable({ items, onSelect, onView }) {
  if (!items.length) return null
  return (
    <div className="elevated rounded-xl overflow-hidden mt-8">
      <div className="px-5 py-3.5 bg-erebus-surface border-b border-white/[0.07]">
        <p className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-wider">Recent OCR History</p>
      </div>
      <table className="w-full">
        <thead>
          <tr className="border-b border-white/[0.05]">
            {['Document', 'Type', 'Size', 'Pages', 'Status', 'Date', ''].map(h => (
              <th key={h} className="px-5 py-2.5 text-left text-[10px] font-mono text-erebus-text-3 uppercase tracking-wider">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map(item => (
            <HistoryRow key={item.id} item={item} onSelect={onSelect} onView={onView} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

function HistoryRow({ item, onSelect, onView }) {
  const [viewLoading, setViewLoading] = useState(false)

  async function handleView(e) {
    e.stopPropagation()
    if (!item.s3_key) return
    setViewLoading(true)
    try {
      const url = await getPresignedUrl(item.s3_key)
      onView(url, item.file_name)
    } catch (err) {
      alert(err.message)
    } finally {
      setViewLoading(false)
    }
  }

  return (
    <tr
      onClick={() => onSelect(item.id)}
      className="border-t border-white/[0.04] hover:bg-erebus-surface-2 transition-colors cursor-pointer group"
    >
      <td className="px-5 py-3">
        <div className="flex items-center gap-2">
          <FileText size={12} className="text-erebus-text-3 shrink-0" />
          <span className="text-[12px] font-medium text-erebus-text-1 truncate max-w-[180px] group-hover:text-erebus-gold transition-colors">
            {item.file_name}
          </span>
        </div>
      </td>
      <td className="px-5 py-3">
        <span className="text-[11px] font-mono text-erebus-text-3">{item.mime_type?.split('/')[1] ?? '—'}</span>
      </td>
      <td className="px-5 py-3">
        <span className="text-[11px] font-mono text-erebus-text-3">{formatBytes(item.file_size)}</span>
      </td>
      <td className="px-5 py-3">
        <span className="text-[11px] font-mono text-erebus-text-3">{item.page_count ?? '—'}</span>
      </td>
      <td className="px-5 py-3">
        <StatusBadge status={item.status} />
      </td>
      <td className="px-5 py-3">
        <span className="text-[11px] font-mono text-erebus-text-3">{formatDate(item.upload_created_at)}</span>
      </td>
      <td className="px-5 py-3">
        {item.s3_key && (
          <button
            onClick={handleView}
            disabled={viewLoading}
            title="Preview file"
            className="flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono text-erebus-text-3 hover:text-erebus-gold hover:bg-erebus-gold/[0.08] transition-colors opacity-0 group-hover:opacity-100 disabled:opacity-40"
          >
            {viewLoading ? <Loader2 size={11} className="animate-spin" /> : <Eye size={11} />}
            Open
          </button>
        )}
      </td>
    </tr>
  )
}

/* ── Main Page ────────────────────────────────────────────────────────────── */
export default function OcrPage() {
  const [activeDoc,      setActiveDoc]      = useState(null)
  const [activeResult,   setActiveResult]   = useState(null)
  const [runningOcr,     setRunningOcr]     = useState(false)
  const [history,        setHistory]        = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [registerError,  setRegisterError]  = useState(null)

  // AI analysis state
  const [analysisData,    setAnalysisData]    = useState(null)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [analysisError,   setAnalysisError]   = useState(null)

  // FileViewer state
  const [viewerUrl,  setViewerUrl]  = useState(null)
  const [viewerName, setViewerName] = useState('')

  const pollRef = useRef(null)

  useEffect(() => { fetchHistory() }, [])
  useEffect(() => () => clearInterval(pollRef.current), [])

  async function fetchHistory() {
    setHistoryLoading(true)
    try {
      const data = await listHistory(1, 20)
      setHistory(data.items ?? [])
    } catch {}
    setHistoryLoading(false)
  }

  const handleUploadSuccess = useCallback(async ({ file_key, file_url }, file) => {
    setRegisterError(null)
    setActiveResult(null)
    setAnalysisData(null)
    setAnalysisError(null)
    try {
      const doc = await registerDocument(
        file?.name ?? file_key.split('/').pop(),
        file_key,
        file?.type ?? 'application/octet-stream',
        file?.size ?? null,
      )
      setActiveDoc(doc)
    } catch (err) {
      setRegisterError(err.message)
    }
  }, [])

  async function handleSelectHistory(docId) {
    try {
      const doc = await getDocument(docId)
      setActiveDoc(doc)
      setActiveResult(null)
      setAnalysisData(null)
      setAnalysisError(null)
      setRegisterError(null)
      if (doc.status === 'completed') {
        const result = await getResult(docId)
        setActiveResult(result)
      } else if (doc.status === 'processing') {
        startPolling(docId)
      }
    } catch (err) {
      setRegisterError(err.message)
    }
  }

  async function handleRunOcr() {
    if (!activeDoc) return
    setRunningOcr(true)
    try {
      await processDocument(activeDoc.id)
      setActiveDoc(prev => ({ ...prev, status: 'processing' }))
      startPolling(activeDoc.id)
    } catch (err) {
      setRegisterError(err.message)
    } finally {
      setRunningOcr(false)
    }
  }

  function startPolling(docId) {
    clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const doc = await getDocument(docId)
        setActiveDoc(doc)
        if (doc.status === 'completed') {
          clearInterval(pollRef.current)
          const result = await getResult(docId)
          setActiveResult(result)
          fetchHistory()
        } else if (doc.status === 'failed') {
          clearInterval(pollRef.current)
          fetchHistory()
        }
      } catch {
        clearInterval(pollRef.current)
      }
    }, POLL_INTERVAL_MS)
  }

  async function handleAnalyse() {
    if (!activeDoc?.id) return
    setAnalysisLoading(true)
    setAnalysisError(null)
    setAnalysisData(null)
    try {
      const res = await analyzeDocument(activeDoc.id)
      setAnalysisData(res)
    } catch (err) {
      setAnalysisError(err.message)
    } finally {
      setAnalysisLoading(false)
    }
  }

  function openViewer(url, name) {
    setViewerUrl(url)
    setViewerName(name)
  }

  const canAnalyse = activeResult && activeDoc?.status === 'completed'

  return (
    <div className="flex-1 overflow-y-auto scrollbar-none bg-erebus-bg">
      <div className="max-w-3xl mx-auto px-6 pt-8 pb-20">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <ScanText size={18} className="text-erebus-gold" />
              <h1 className="font-serif text-[26px] text-erebus-text-1">OCR & Analysis</h1>
            </div>
            <p className="text-[12px] font-mono text-erebus-text-3">
              Upload a document → extract text → analyse with AI models
            </p>
          </div>
          <button
            id="ocr-refresh-history"
            onClick={fetchHistory}
            disabled={historyLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-medium btn-ghost"
          >
            <RefreshCw size={13} className={historyLoading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>

        {/* Upload Zone */}
        {!activeDoc && (
          <section className="mb-6">
            <FileUploader
              prefix="ocr-uploads"
              onSuccess={handleUploadSuccess}
              label="Drop a document here, or click to browse"
            />
            {registerError && (
              <p className="mt-2 text-[12px] font-mono text-erebus-red">{registerError}</p>
            )}
            <p className="mt-2 text-[11px] font-mono text-erebus-text-3">
              Supported: PDF · JPEG · PNG · max 50 MB
            </p>
          </section>
        )}

        {/* Active document flow */}
        {activeDoc && (
          <section className="space-y-5 mb-6">
            <button
              id="ocr-new-upload"
              onClick={() => {
                setActiveDoc(null)
                setActiveResult(null)
                setAnalysisData(null)
                setAnalysisError(null)
                setRegisterError(null)
                clearInterval(pollRef.current)
              }}
              className="flex items-center gap-1.5 text-[12px] font-mono text-erebus-text-3 hover:text-erebus-text-2 transition-colors"
            >
              <Upload size={12} />
              Upload a different file
            </button>

            <DocumentCard
              doc={activeDoc}
              onRunOcr={handleRunOcr}
              running={runningOcr}
              onView={openViewer}
            />

            {activeDoc.status === 'processing' && !activeResult && (
              <div className="flex items-center gap-3 px-5 py-4 rounded-xl bg-erebus-amber/[0.06] border border-erebus-amber/[0.15]">
                <Loader2 size={16} className="text-erebus-amber animate-spin shrink-0" />
                <div>
                  <p className="text-[13px] font-medium text-erebus-text-1">OCR is running…</p>
                  <p className="text-[11px] font-mono text-erebus-text-3 mt-0.5">
                    Polling for results every 3s. This usually takes 5–30 seconds.
                  </p>
                </div>
              </div>
            )}

            {activeResult && (
              <ResultViewer result={activeResult} doc={activeDoc} />
            )}

                        {/* ── Analyse ── */}
            {canAnalyse && !analysisData && (
              <div className="flex items-center gap-3">
                <button
                  id="ocr-analyse-button"
                  onClick={handleAnalyse}
                  disabled={analysisLoading}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-erebus-gold/[0.12] border border-erebus-gold/30 text-erebus-gold text-[13px] font-semibold hover:bg-erebus-gold/[0.22] transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {analysisLoading
                    ? <><Loader2 size={14} className="animate-spin" /> Analysing…</>
                    : <><Brain size={14} /> Analyse
                      <span className="ml-1.5 text-[10px] font-mono opacity-60 font-normal tracking-wide">via OpenAI</span>
                    </>
                  }
                </button>
                <p className="text-[11px] font-mono text-erebus-text-3">
                  Summary · entities · sentiment · action items
                </p>
              </div>
            )}

            {analysisLoading && (
              <div className="flex items-center gap-3 px-5 py-4 rounded-xl bg-erebus-gold/[0.05] border border-erebus-gold/[0.15]">
                <Loader2 size={16} className="text-erebus-gold animate-spin shrink-0" />
                <div>
                  <p className="text-[13px] font-medium text-erebus-text-1">Analysing document with OpenAI…</p>
                  <p className="text-[11px] font-mono text-erebus-text-3 mt-0.5">
                    Extracting summary, entities &amp; sentiment. Usually takes 5–15s.
                  </p>
                </div>
              </div>
            )}

            {analysisError && (
              <div className="flex items-start gap-3 px-4 py-3 rounded-lg bg-erebus-red/[0.06] border border-erebus-red/20">
                <AlertCircle size={14} className="text-erebus-red mt-0.5 shrink-0" />
                <p className="text-[12px] font-mono text-erebus-red">{analysisError}</p>
              </div>
            )}

            {analysisData && (
              <AnalysisPanel
                data={analysisData}
                onDismiss={() => setAnalysisData(null)}
              />
            )}

            {registerError && (
              <p className="text-[12px] font-mono text-erebus-red">{registerError}</p>
            )}
          </section>
        )}

        {!activeDoc && history.length === 0 && !historyLoading && (
          <div className="py-16 flex flex-col items-center text-center">
            <div className="w-14 h-14 rounded-2xl bg-erebus-gold/[0.08] border border-erebus-gold/20 flex items-center justify-center mb-4">
              <ScanText size={24} className="text-erebus-gold opacity-60" />
            </div>
            <p className="text-[15px] font-medium text-erebus-text-2 mb-1">No documents yet</p>
            <p className="text-[12px] font-mono text-erebus-text-3">
              Upload a PDF or image above to extract and analyse text
            </p>
          </div>
        )}

        {historyLoading && history.length === 0 ? (
          <div className="flex items-center gap-2 mt-8 text-[12px] font-mono text-erebus-text-3">
            <Loader2 size={13} className="animate-spin" /> Loading history…
          </div>
        ) : (
          <HistoryTable items={history} onSelect={handleSelectHistory} onView={openViewer} />
        )}

      </div>

      {/* FileViewer modal */}
      <FileViewer
        url={viewerUrl}
        fileName={viewerName}
        onClose={() => { setViewerUrl(null); setViewerName('') }}
      />
    </div>
  )
}
