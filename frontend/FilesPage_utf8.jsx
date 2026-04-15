// src/pages/app/FilesPage.jsx
import { useState, useCallback, useEffect } from 'react'
import {
  FileText, FileImage, FileSpreadsheet, Trash2, Clock,
  CheckCircle, AlertCircle, Loader2, Eye, RefreshCw, Database,
} from 'lucide-react'
import FileUploader from '../../components/ui/FileUploader'
import FileViewer   from '../../components/ui/FileViewer'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

/* ΓöÇΓöÇ Status config ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */
const STATUS_META = {
  indexed:    { icon: CheckCircle, cls: 'text-erebus-green', label: 'Indexed'    },
  processing: { icon: Clock,       cls: 'text-erebus-amber', label: 'Processing' },
  failed:     { icon: AlertCircle, cls: 'text-erebus-red',   label: 'Failed'     },
}

/* ΓöÇΓöÇ File type helpers ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */
function getExt(name = '') { return name.split('.').pop().toLowerCase() }

function FileTypeIcon({ name }) {
  const ext = getExt(name)
  if (ext === 'pdf') return <FileText size={12} className="text-erebus-red" />
  if (['jpg','jpeg','png','gif','webp','bmp','svg'].includes(ext))
    return <FileImage size={12} className="text-erebus-blue" />
  if (['csv','xlsx','xls','xlsm'].includes(ext))
    return <FileSpreadsheet size={12} className="text-erebus-green" />
  return <FileText size={12} className="text-erebus-blue" />
}

function getViewerLabel(name = '') {
  const ext = getExt(name)
  if (ext === 'pdf')  return 'Preview PDF'
  if (['jpg','jpeg','png','gif','webp','bmp','svg'].includes(ext)) return 'View image'
  if (['csv','xlsx','xls'].includes(ext)) return 'Open spreadsheet'
  return 'Open file'
}

/* ΓöÇΓöÇ Format helpers ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */
function formatBytes(bytes) {
  if (!bytes) return 'ΓÇö'
  const k = 1024, sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}

function formatDate(iso) {
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

/* ΓöÇΓöÇ File row ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */
function FileRow({ file, onDelete, onOpen }) {
  const [deleting, setDeleting]  = useState(false)
  const [opening,  setOpening]   = useState(false)

  const name   = file.name ?? file.file_key?.split('/').pop() ?? 'ΓÇö'
  const status = file.status ?? 'indexed'
  const sm     = STATUS_META[status] ?? STATUS_META.indexed
  const Icon   = sm.icon

  async function handleDelete() {
    if (!window.confirm(`Delete "${name}"?`)) return
    setDeleting(true)
    await onDelete(file.file_key)
    setDeleting(false)
  }

  async function handleOpen() {
    setOpening(true)
    await onOpen(file.file_key, name)
    setOpening(false)
  }

  return (
    <tr className="border-t border-white/[0.05] group hover:bg-erebus-surface-2 transition-colors">
      {/* Filename */}
      <td className="px-5 py-3.5">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-erebus-surface border border-white/[0.08] flex items-center justify-center shrink-0">
            <FileTypeIcon name={name} />
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
      </td>

      {/* Size */}
      <td className="px-5 py-3.5 font-mono text-[12px] text-erebus-text-3">
        {file.size ?? formatBytes(file.size_bytes)}
      </td>

      {/* Uploaded */}
      <td className="px-5 py-3.5 font-mono text-[12px] text-erebus-text-3">
        {file.date ?? formatDate(file.last_modified)}
      </td>

      {/* Status */}
      <td className="px-5 py-3.5">
        <div className="flex items-center gap-1.5">
          <Icon size={12} className={sm.cls} />
          <span className={`text-[11px] font-mono ${sm.cls}`}>{sm.label}</span>
        </div>
      </td>

      {/* Actions */}
      <td className="px-5 py-3.5">
        <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
          {/* Open / Preview */}
          <button
            onClick={handleOpen}
            disabled={opening}
            title={getViewerLabel(name)}
            className="flex items-center gap-1 px-2 py-1 rounded text-[11px] font-mono text-erebus-text-3 hover:text-erebus-gold hover:bg-erebus-gold/[0.08] transition-colors disabled:opacity-40"
          >
            {opening
              ? <Loader2 size={12} className="animate-spin" />
              : <Eye size={12} />
            }
            <span>Open</span>
          </button>

          {/* Delete */}
          <button
            onClick={handleDelete}
            disabled={deleting}
            title="Delete file"
            className="p-1 rounded text-erebus-text-3 hover:text-erebus-red transition-colors disabled:opacity-40"
          >
            {deleting ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
          </button>
        </div>
      </td>
    </tr>
  )
}

/* ΓöÇΓöÇ Main Page ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ */
export default function FilesPage() {
  const [s3Files,     setS3Files]     = useState([])
  const [s3Loading,   setS3Loading]   = useState(false)
  const [s3Error,     setS3Error]     = useState(null)
  const [uploadCount, setUploadCount] = useState(0)

  // Viewer state
  const [viewerUrl,  setViewerUrl]  = useState(null)
  const [viewerName, setViewerName] = useState('')

  /* Load S3 file list ΓÇö both uploads/ and ocr-uploads/ folders */
  const fetchFiles = useCallback(async () => {
    setS3Loading(true)
    setS3Error(null)
    try {
      const [r1, r2] = await Promise.all([
        fetch(`${API_BASE}/uploads/files?prefix=uploads&max_keys=200`),
        fetch(`${API_BASE}/uploads/files?prefix=ocr-uploads&max_keys=200`),
      ])
      const [d1, d2] = await Promise.all([r1.json(), r2.json()])
      const merged = [...(d1.files ?? []), ...(d2.files ?? [])]
      merged.sort((a, b) => new Date(b.last_modified) - new Date(a.last_modified))
      setS3Files(merged)
    } catch (err) {
      setS3Error(err.message)
    } finally {
      setS3Loading(false)
    }
  }, [])

  useEffect(() => { fetchFiles() }, [fetchFiles, uploadCount])

  /* Delete */
  const handleDelete = useCallback(async (fileKey) => {
    try {
      const res = await fetch(`${API_BASE}/uploads/file`, {
        method:  'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ file_key: fileKey }),
      })
      if (!res.ok) throw new Error(`Delete failed: ${res.status}`)
      setS3Files(prev => prev.filter(f => f.file_key !== fileKey))
    } catch (err) {
      alert(`Could not delete file: ${err.message}`)
    }
  }, [])

  /* Open ΓÇö get presigned URL then show viewer */
  const handleOpen = useCallback(async (fileKey, fileName) => {
    try {
      const res = await fetch(`${API_BASE}/uploads/generate-download-url`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ file_key: fileKey }),
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
    <div className="flex-1 overflow-y-auto scrollbar-none bg-erebus-bg">
      <div className="max-w-4xl mx-auto px-6 pt-8 pb-20">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Database size={18} className="text-erebus-gold" />
              <h1 className="font-serif text-[26px] text-erebus-text-1">My Files</h1>
            </div>
            <p className="text-[12px] font-mono text-erebus-text-3">
              {s3Loading
                ? 'LoadingΓÇª'
                : s3Error
                  ? 'Could not load file list'
                  : `${s3Files.length} documents in S3`
              }
            </p>
          </div>
          <button
            onClick={fetchFiles}
            disabled={s3Loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-medium btn-ghost"
          >
            <RefreshCw size={13} className={s3Loading ? 'animate-spin' : ''} />
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
                    <p className="text-[12px] font-mono text-erebus-text-3">Loading from S3ΓÇª</p>
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
                  <FileRow
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
            Files stored in S3 ┬╖ Download links expire in 1 hour
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
