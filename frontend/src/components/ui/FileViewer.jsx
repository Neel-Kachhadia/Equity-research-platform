/**
 * FileViewer.jsx — Universal file viewer modal
 * Supports: PDF, CSV, XLSX, images
 */
import { useState, useEffect } from 'react'
import {
  X, ChevronLeft, ChevronRight,
  ZoomIn, ZoomOut, Download, Loader2,
  AlertCircle, FileSpreadsheet, Image as ImageIcon, FileText,
} from 'lucide-react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'
import * as XLSX from 'xlsx'

// Point pdfjs at the bundled worker
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

/* ── Helpers ─────────────────────────────────────────────────────────────── */
function getFileType(name = '') {
  const ext = name.split('.').pop().toLowerCase()
  if (ext === 'pdf')                                            return 'pdf'
  if (['jpg','jpeg','png','gif','webp','bmp','svg'].includes(ext)) return 'image'
  if (ext === 'csv')                                            return 'csv'
  if (['xlsx','xls','xlsm'].includes(ext))                     return 'xlsx'
  return 'unknown'
}

/* ── Utility panels ──────────────────────────────────────────────────────── */
function LoadingPane({ label = 'Loading…' }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3 text-erebus-text-3">
      <Loader2 size={28} className="animate-spin text-erebus-gold" />
      <span className="text-[12px] font-mono">{label}</span>
    </div>
  )
}

function ErrorPane({ msg, url, fileName }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 text-erebus-red px-6">
      <AlertCircle size={32} className="opacity-70" />
      <p className="text-[13px] font-mono text-center max-w-md">{msg}</p>
      {url && (
        <a
          href={url}
          download={fileName}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-erebus-gold/10 text-erebus-gold text-[13px] hover:bg-erebus-gold/20 transition-colors"
        >
          <Download size={14} /> Download file instead
        </a>
      )}
    </div>
  )
}

/* ── CSV / XLSX Table viewer ─────────────────────────────────────────────── */
function TableViewer({ url, type }) {
  const [rows,    setRows]    = useState([])
  const [headers, setHeaders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)
  const [page,    setPage]    = useState(0)
  const PAGE_SIZE = 100

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    setRows([])
    setHeaders([])
    setPage(0)

    async function load() {
      try {
        const res = await fetch(url, { mode: 'cors' })
        if (!res.ok) throw new Error(`HTTP ${res.status} fetching file`)
        const buf = await res.arrayBuffer()
        if (cancelled) return

        if (type === 'csv') {
          const { default: Papa } = await import('papaparse')
          const text   = new TextDecoder().decode(buf)
          const result = Papa.parse(text, { header: true, skipEmptyLines: true })
          if (!cancelled) {
            setHeaders(result.meta.fields || [])
            setRows(result.data)
          }
        } else {
          // XLSX — static import, no dynamic crash risk
          const wb   = XLSX.read(buf, { type: 'array' })
          const ws   = wb.Sheets[wb.SheetNames[0]]
          const data = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' })
          if (!cancelled) {
            setHeaders((data[0] || []).map(String))
            setRows(data.slice(1))
          }
        }
      } catch (e) {
        console.error('[FileViewer] TableViewer error:', e)
        if (!cancelled) setError(e.message || 'Failed to load file')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [url, type])

  if (loading) return <LoadingPane label={type === 'csv' ? 'Parsing CSV…' : 'Parsing spreadsheet…'} />
  if (error)   return <ErrorPane msg={error} url={url} />

  const totalPages = Math.ceil(rows.length / PAGE_SIZE)
  const pageRows   = rows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  if (rows.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-erebus-text-3">
        <FileSpreadsheet size={32} className="opacity-30" />
        <p className="text-[13px] font-mono">No data rows found in this file.</p>
        <a href={url} download target="_blank" rel="noreferrer"
           className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-erebus-gold/10 text-erebus-gold text-[12px] hover:bg-erebus-gold/20 transition-colors">
          <Download size={13} /> Download to open locally
        </a>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="overflow-auto flex-1">
        <table className="w-full text-[12px] border-collapse">
          <thead className="sticky top-0 bg-erebus-surface z-10">
            <tr>
              {headers.map((h, i) => (
                <th key={i} className="px-3 py-2 text-left font-mono text-[11px] text-erebus-text-3 border-b border-white/[0.07] whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, ri) => (
              <tr key={ri} className="border-t border-white/[0.04] hover:bg-white/[0.02]">
                {headers.map((h, ci) => (
                  <td key={ci} className="px-3 py-1.5 text-erebus-text-2 whitespace-nowrap max-w-[200px] truncate">
                    {Array.isArray(row) ? String(row[ci] ?? '') : String(row[h] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-2 border-t border-white/[0.07] bg-erebus-surface text-[11px] font-mono text-erebus-text-3 shrink-0">
          <span>{rows.length} rows · page {page + 1}/{totalPages}</span>
          <div className="flex gap-2">
            <button disabled={page === 0} onClick={() => setPage(p => p - 1)}
              className="px-2 py-0.5 rounded disabled:opacity-30 hover:text-erebus-gold">← Prev</button>
            <button disabled={page === totalPages - 1} onClick={() => setPage(p => p + 1)}
              className="px-2 py-0.5 rounded disabled:opacity-30 hover:text-erebus-gold">Next →</button>
          </div>
        </div>
      )}
    </div>
  )
}

/* ── PDF viewer ───────────────────────────────────────────────────────────── */
function PdfViewer({ url }) {
  const [numPages, setNumPages] = useState(null)
  const [pageNum,  setPageNum]  = useState(1)
  const [scale,    setScale]    = useState(1.2)
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState(null)

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/[0.07] bg-erebus-surface text-[11px] font-mono text-erebus-text-3 shrink-0">
        <div className="flex items-center gap-3">
          <button disabled={pageNum <= 1} onClick={() => setPageNum(p => p - 1)}
            className="p-1 rounded disabled:opacity-30 hover:text-erebus-text-1">
            <ChevronLeft size={14} />
          </button>
          <span>{loading ? '…' : `${pageNum} / ${numPages ?? '?'}`}</span>
          <button disabled={!numPages || pageNum >= numPages} onClick={() => setPageNum(p => p + 1)}
            className="p-1 rounded disabled:opacity-30 hover:text-erebus-text-1">
            <ChevronRight size={14} />
          </button>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setScale(s => Math.max(0.5, s - 0.2))}
            className="p-1 rounded hover:text-erebus-gold"><ZoomOut size={14} /></button>
          <span>{Math.round(scale * 100)}%</span>
          <button onClick={() => setScale(s => Math.min(3, s + 0.2))}
            className="p-1 rounded hover:text-erebus-gold"><ZoomIn size={14} /></button>
        </div>
      </div>

      <div className="flex-1 overflow-auto flex justify-center bg-erebus-bg/50 py-4">
        {error ? <ErrorPane msg={error} url={url} /> : (
          <Document
            file={url}
            onLoadSuccess={({ numPages }) => { setNumPages(numPages); setLoading(false) }}
            onLoadError={e => { console.error('[FileViewer] PDF error:', e); setError(e.message); setLoading(false) }}
            loading={<LoadingPane label="Loading PDF…" />}
          >
            <Page
              pageNumber={pageNum}
              scale={scale}
              className="shadow-xl rounded"
              loading={<LoadingPane label="Rendering page…" />}
            />
          </Document>
        )}
      </div>
    </div>
  )
}

/* ── Image viewer ─────────────────────────────────────────────────────────── */
function ImageViewer({ url, fileName }) {
  const [scale, setScale] = useState(1)
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-center gap-3 px-4 py-2 border-b border-white/[0.07] bg-erebus-surface text-[11px] font-mono text-erebus-text-3 shrink-0">
        <button onClick={() => setScale(s => Math.max(0.2, s - 0.2))} className="p-1 hover:text-erebus-gold"><ZoomOut size={14} /></button>
        <span>{Math.round(scale * 100)}%</span>
        <button onClick={() => setScale(s => Math.min(5, s + 0.2))} className="p-1 hover:text-erebus-gold"><ZoomIn size={14} /></button>
        <button onClick={() => setScale(1)} className="px-2 py-0.5 rounded hover:text-erebus-gold">Reset</button>
      </div>
      <div className="flex-1 overflow-auto flex items-center justify-center p-6 bg-erebus-bg/50">
        <img
          src={url}
          alt={fileName}
          style={{ transform: `scale(${scale})`, transformOrigin: 'center', transition: 'transform 0.15s' }}
          className="max-w-full shadow-2xl rounded"
        />
      </div>
    </div>
  )
}

/* ── Unsupported ──────────────────────────────────────────────────────────── */
function UnsupportedViewer({ url, fileName }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 text-erebus-text-3">
      <FileText size={48} className="opacity-20" />
      <p className="text-[13px]">Preview not available for this file type.</p>
      <a href={url} download={fileName} target="_blank" rel="noreferrer"
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-erebus-gold/10 text-erebus-gold text-[13px] hover:bg-erebus-gold/20 transition-colors">
        <Download size={14} /> Download file
      </a>
    </div>
  )
}

/* ── File type icon ──────────────────────────────────────────────────────── */
function FileTypeIcon({ type }) {
  if (type === 'pdf')                      return <FileText size={14} className="text-erebus-red" />
  if (type === 'image')                    return <ImageIcon size={14} className="text-erebus-blue" />
  if (type === 'csv' || type === 'xlsx')   return <FileSpreadsheet size={14} className="text-erebus-green" />
  return <FileText size={14} className="text-erebus-text-3" />
}

/* ── Main modal ──────────────────────────────────────────────────────────── */
export default function FileViewer({ url, fileName = '', onClose }) {
  const fileType = getFileType(fileName)

  useEffect(() => {
    const handler = e => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  if (!url) return null

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="relative flex flex-col w-full max-w-5xl bg-erebus-surface rounded-2xl border border-white/[0.08] shadow-2xl overflow-hidden"
           style={{ height: '90vh' }}>

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-white/[0.07] bg-erebus-surface shrink-0">
          <div className="flex items-center gap-2.5 min-w-0">
            <FileTypeIcon type={fileType} />
            <span className="text-[13px] font-medium text-erebus-text-1 truncate max-w-[400px]">
              {fileName || 'File Preview'}
            </span>
            <span className="text-[10px] font-mono text-erebus-text-3 uppercase px-1.5 py-0.5 rounded bg-white/[0.05] shrink-0">
              {fileType}
            </span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <a href={url} download={fileName} target="_blank" rel="noreferrer" title="Download"
               className="p-1.5 rounded-lg text-erebus-text-3 hover:text-erebus-gold hover:bg-white/[0.05] transition-colors">
              <Download size={15} />
            </a>
            <button onClick={onClose}
               className="p-1.5 rounded-lg text-erebus-text-3 hover:text-erebus-text-1 hover:bg-white/[0.05] transition-colors">
              <X size={15} />
            </button>
          </div>
        </div>

        {/* Viewer body — explicit height so table can scroll */}
        <div className="flex-1 overflow-hidden">
          {fileType === 'pdf'                           && <PdfViewer url={url} />}
          {fileType === 'image'                         && <ImageViewer url={url} fileName={fileName} />}
          {(fileType === 'csv' || fileType === 'xlsx')  && <TableViewer url={url} type={fileType} />}
          {fileType === 'unknown'                       && <UnsupportedViewer url={url} fileName={fileName} />}
        </div>
      </div>
    </div>
  )
}
