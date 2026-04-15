/**
 * src/components/ui/FileUploader.jsx
 *
 * Production-grade file upload component.
 * - Dropzone + click-to-browse
 * - Real-time progress bar
 * - Status indicators (idle / uploading / done / error)
 * - Copy URL button after successful upload
 * - Cancel support
 * - Multi-file awareness
 * Uses: useFileUpload hook (presigned S3 architecture)
 */

import { useCallback, useRef } from 'react'
import { useDropzone } from 'react-dropzone'
import {
  Upload, X, CheckCircle, AlertCircle,
  Loader, Copy, ExternalLink, FileText,
} from 'lucide-react'
import { useFileUpload, ALLOWED_TYPES, MAX_FILE_SIZE } from '../../hooks/useFileUpload'

// ── Helpers ──────────────────────────────────────────────────────────────────
function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}

function copyToClipboard(text) {
  navigator.clipboard?.writeText(text).catch(() => {})
}

// ── Sub-components ────────────────────────────────────────────────────────────

function ProgressBar({ progress, phase }) {
  const colorClass =
    phase === 'done'  ? 'bg-erebus-green' :
    phase === 'error' ? 'bg-erebus-red' :
    'bg-erebus-gold'

  return (
    <div className="w-full h-1.5 rounded-full bg-white/[0.07] overflow-hidden mt-3">
      <div
        className={`h-full rounded-full transition-all duration-300 ease-out ${colorClass}`}
        style={{ width: `${progress}%` }}
      />
    </div>
  )
}

function StatusBadge({ phase, error }) {
  if (phase === 'idle') return null

  const config = {
    requesting: { icon: Loader,       cls: 'text-erebus-text-3', spin: true,  label: 'Requesting upload URL…' },
    uploading:  { icon: Loader,       cls: 'text-erebus-gold',   spin: true,  label: 'Uploading to S3…'        },
    done:       { icon: CheckCircle,  cls: 'text-erebus-green',  spin: false, label: 'Upload complete'          },
    error:      { icon: AlertCircle,  cls: 'text-erebus-red',    spin: false, label: error ?? 'Upload failed'  },
  }[phase]

  if (!config) return null
  const Icon = config.icon

  return (
    <div className={`flex items-center gap-2 text-[12px] font-mono mt-2 ${config.cls}`}>
      <Icon size={13} className={config.spin ? 'animate-spin' : ''} />
      <span>{config.label}</span>
    </div>
  )
}

function SuccessPanel({ fileKey, fileUrl, onReset }) {
  return (
    <div className="mt-4 rounded-xl border border-erebus-green/20 bg-erebus-green/[0.05] p-4">
      <div className="flex items-center gap-2 mb-3">
        <CheckCircle size={14} className="text-erebus-green" />
        <p className="text-[13px] font-medium text-erebus-green">File uploaded successfully</p>
      </div>

      <div className="space-y-2">
        {/* File URL */}
        <div className="flex items-center gap-2 bg-erebus-bg rounded-lg px-3 py-2">
          <span className="text-[11px] font-mono text-erebus-text-3 shrink-0">URL</span>
          <span className="text-[12px] font-mono text-erebus-text-2 flex-1 truncate">{fileUrl}</span>
          <button
            onClick={() => copyToClipboard(fileUrl)}
            title="Copy URL"
            className="text-erebus-text-3 hover:text-erebus-gold transition-colors shrink-0"
          >
            <Copy size={12} />
          </button>
          <a
            href={fileUrl}
            target="_blank"
            rel="noreferrer"
            title="Open file"
            className="text-erebus-text-3 hover:text-erebus-blue transition-colors shrink-0"
          >
            <ExternalLink size={12} />
          </a>
        </div>

        {/* File Key */}
        <div className="flex items-center gap-2 bg-erebus-bg rounded-lg px-3 py-2">
          <span className="text-[11px] font-mono text-erebus-text-3 shrink-0">Key</span>
          <span className="text-[12px] font-mono text-erebus-text-2 flex-1 truncate">{fileKey}</span>
          <button
            onClick={() => copyToClipboard(fileKey)}
            title="Copy key"
            className="text-erebus-text-3 hover:text-erebus-gold transition-colors shrink-0"
          >
            <Copy size={12} />
          </button>
        </div>
      </div>

      <button
        onClick={onReset}
        className="mt-3 text-[11px] font-mono text-erebus-text-3 hover:text-erebus-text-2 underline"
      >
        Upload another file
      </button>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

/**
 * @param {Object}   props
 * @param {string}   [props.prefix="uploads"]     S3 key prefix
 * @param {Object}   [props.metadata]             Extra S3 object metadata
 * @param {Function} [props.onSuccess]            Called with { file_key, file_url } on done
 * @param {string}   [props.label]                Drop-zone label override
 * @param {boolean}  [props.compact]              Smaller, inline variant
 */
export default function FileUploader({
  prefix    = 'uploads',
  metadata  = null,
  onSuccess = null,
  label     = 'Drop files here or click to browse',
  compact   = false,
}) {
  const { status, upload, cancel, reset } = useFileUpload({ prefix, metadata })
  const { phase, progress, error, file_key, file_url } = status

  const busy = phase === 'requesting' || phase === 'uploading'

  const onDrop = useCallback(async (acceptedFiles) => {
    if (!acceptedFiles.length || busy) return
    const file = acceptedFiles[0]
    const result = await upload(file)
    if (result && onSuccess) onSuccess(result, file)
  }, [busy, upload, onSuccess])

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    disabled:  busy,
    maxFiles:  1,
    maxSize:   MAX_FILE_SIZE,
    accept:    Object.fromEntries(Object.keys(ALLOWED_TYPES).map(t => [t, []])),
  })

  // Show success panel when done
  if (phase === 'done' && file_key && file_url) {
    return <SuccessPanel fileKey={file_key} fileUrl={file_url} onReset={reset} />
  }

  return (
    <div className="w-full">
      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`
          relative rounded-xl border-2 border-dashed transition-all duration-200 cursor-pointer
          ${compact ? 'px-4 py-5' : 'px-6 py-10'}
          ${busy
            ? 'border-erebus-gold/30 bg-erebus-gold/[0.03] cursor-not-allowed pointer-events-none'
            : isDragActive
              ? 'border-erebus-gold/60 bg-erebus-gold/[0.06] shadow-[0_0_0_4px_rgba(201,168,76,0.08)]'
              : 'border-white/[0.10] bg-erebus-surface hover:border-white/[0.18] hover:bg-erebus-surface-2'
          }
          ${phase === 'error' ? '!border-erebus-red/40 !bg-erebus-red/[0.04]' : ''}
        `}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center gap-3 text-center pointer-events-none select-none">
          {busy ? (
            <Loader size={compact ? 20 : 28} className="text-erebus-gold animate-spin" />
          ) : phase === 'error' ? (
            <AlertCircle size={compact ? 20 : 28} className="text-erebus-red" />
          ) : (
            <div className={`rounded-xl bg-white/[0.05] flex items-center justify-center ${compact ? 'w-10 h-10' : 'w-14 h-14'}`}>
              <Upload size={compact ? 16 : 22} className={isDragActive ? 'text-erebus-gold' : 'text-erebus-text-3'} />
            </div>
          )}

          <div>
            <p className={`font-medium text-erebus-text-1 ${compact ? 'text-[13px]' : 'text-[15px]'}`}>
              {busy
                ? `Uploading… ${progress}%`
                : isDragActive
                  ? 'Drop to upload'
                  : phase === 'error'
                    ? 'Upload failed — try again'
                    : label
              }
            </p>
            {!busy && phase !== 'error' && (
              <p className="text-[11px] font-mono text-erebus-text-3 mt-1">
                PDF · TXT · CSV · XLSX · PNG · JPG · JSON · max 50 MB
              </p>
            )}
          </div>
        </div>

        {/* Progress bar inside zone */}
        {busy && (
          <div className="absolute bottom-0 left-0 right-0 h-1 rounded-b-xl bg-white/[0.04] overflow-hidden">
            <div
              className="h-full bg-erebus-gold transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </div>

      {/* Dropzone rejection messages */}
      {fileRejections.length > 0 && (
        <div className="mt-2 space-y-1">
          {fileRejections.map(({ file, errors }) => (
            <p key={file.name} className="text-[11px] font-mono text-erebus-red">
              {file.name}: {errors.map(e => e.message).join(' · ')}
            </p>
          ))}
        </div>
      )}

      {/* Status (outside zone) */}
      <StatusBadge phase={phase} error={error} />
      {(phase === 'uploading' || phase === 'requesting') && (
        <ProgressBar progress={progress} phase={phase} />
      )}

      {/* Cancel button */}
      {busy && (
        <button
          onClick={(e) => { e.stopPropagation(); cancel() }}
          className="mt-2 flex items-center gap-1.5 text-[11px] font-mono text-erebus-text-3 hover:text-erebus-red transition-colors"
        >
          <X size={11} /> Cancel upload
        </button>
      )}

      {/* Retry on error */}
      {phase === 'error' && (
        <button
          onClick={reset}
          className="mt-2 text-[11px] font-mono text-erebus-text-3 hover:text-erebus-text-2 underline"
        >
          Try again
        </button>
      )}
    </div>
  )
}
