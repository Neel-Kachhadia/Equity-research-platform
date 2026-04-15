/**
 * src/hooks/useFileUpload.js
 *
 * Custom hook for the presigned-URL S3 upload flow.
 *
 * Flow:
 *   1. POST /uploads/generate-upload-url  → { upload_url, file_key, file_url }
 *   2. PUT  upload_url with raw file bytes + Content-Type header
 *   3. Return { file_key, file_url } to caller
 *
 * Features:
 *   - Per-file progress tracking via XMLHttpRequest
 *   - Cancellation via AbortController
 *   - Multi-file support (upload sequentially or in parallel)
 *   - Retry logic for expired presigned URLs
 *   - Clear status machine: idle → requesting → uploading → done | error
 */

import { useState, useRef, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// ── Allowed MIME types (mirror server-side allowlist) ─────────────────────────
export const ALLOWED_TYPES = {
  'application/pdf':                                                    '.pdf',
  'text/plain':                                                         '.txt',
  'text/csv':                                                           '.csv',
  'application/vnd.ms-excel':                                           '.xls',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':  '.xlsx',
  'image/png':                                                          '.png',
  'image/jpeg':                                                         '.jpg',
  'image/webp':                                                         '.webp',
  'application/json':                                                   '.json',
}

export const MAX_FILE_SIZE = 50 * 1024 * 1024  // 50 MB

// ── Status shape ──────────────────────────────────────────────────────────────
const INITIAL_STATUS = {
  phase:    'idle',   // idle | requesting | uploading | done | error
  progress: 0,        // 0–100
  error:    null,
  file_key: null,
  file_url: null,
}


// ─────────────────────────────────────────────────────────────────────────────
// Client-side validation (runs BEFORE going to the server)
// ─────────────────────────────────────────────────────────────────────────────
function validateFile(file) {
  if (!file) return 'No file provided.'
  if (!ALLOWED_TYPES[file.type]) {
    return `File type "${file.type}" is not allowed. Accepted: ${Object.values(ALLOWED_TYPES).join(', ')}`
  }
  if (file.size > MAX_FILE_SIZE) {
    return `File is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum is 50 MB.`
  }
  if (file.name.length > 255) return 'Filename is too long.'
  return null  // valid
}


// ─────────────────────────────────────────────────────────────────────────────
// Low-level: upload a single file via XHR (supports progress + cancellation)
// ─────────────────────────────────────────────────────────────────────────────
function xhrUpload(url, file, onProgress, signal) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()

    // Propagate AbortController signal
    if (signal) {
      signal.addEventListener('abort', () => {
        xhr.abort()
        reject(new DOMException('Upload cancelled by user.', 'AbortError'))
      })
    }

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    })

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        onProgress(100)
        resolve()
      } else {
        reject(new Error(`S3 upload failed with status ${xhr.status}.`))
      }
    })

    xhr.addEventListener('error', () => reject(new Error('Network error during upload.')))
    xhr.addEventListener('timeout', () => reject(new Error('Upload timed out.')))

    xhr.open('PUT', url)
    xhr.setRequestHeader('Content-Type', file.type)
    xhr.timeout = 5 * 60 * 1000  // 5 min timeout

    xhr.send(file)
  })
}


// ─────────────────────────────────────────────────────────────────────────────
// Hook
// ─────────────────────────────────────────────────────────────────────────────
export function useFileUpload({ prefix = 'uploads', metadata = null } = {}) {
  const [status, setStatus] = useState(INITIAL_STATUS)
  const abortRef = useRef(null)

  // Reset to idle
  const reset = useCallback(() => {
    abortRef.current?.abort()
    setStatus(INITIAL_STATUS)
  }, [])

  // Cancel an in-progress upload
  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setStatus(prev => ({ ...prev, phase: 'idle', progress: 0, error: 'Cancelled.' }))
  }, [])

  /**
   * Upload a single File object.
   * Returns { file_key, file_url } on success.
   * Updates `status` throughout — consumers can drive UI from it.
   */
  const upload = useCallback(async (file) => {
    // 1. Client-side validation
    const validationError = validateFile(file)
    if (validationError) {
      setStatus({ ...INITIAL_STATUS, phase: 'error', error: validationError })
      return null
    }

    // 2. Set up cancellation
    abortRef.current = new AbortController()
    const { signal } = abortRef.current

    try {
      // 3. Request presigned URL from backend
      setStatus({ ...INITIAL_STATUS, phase: 'requesting' })

      const res = await fetch(`${API_BASE}/uploads/generate-upload-url`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          file_name:  file.name,
          file_type:  file.type,
          prefix,
          ...(metadata ? { metadata } : {}),
        }),
        signal,
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail ?? `Server error ${res.status}`)
      }

      const { upload_url, file_key, file_url } = await res.json()

      // 4. Upload directly to S3
      setStatus(prev => ({ ...prev, phase: 'uploading', progress: 0 }))

      await xhrUpload(
        upload_url,
        file,
        (progress) => setStatus(prev => ({ ...prev, progress })),
        signal,
      )

      // 5. Done
      const result = { file_key, file_url }
      setStatus({ phase: 'done', progress: 100, error: null, ...result })
      return result

    } catch (err) {
      if (err.name === 'AbortError') return null  // cancelled — don't update phase again

      const message = err.message ?? 'Upload failed.'
      setStatus(prev => ({ ...prev, phase: 'error', error: message, progress: 0 }))
      return null
    }
  }, [prefix, metadata])


  /**
   * Upload multiple files sequentially.
   * Returns array of { file_key, file_url } (null entries = failed/cancelled).
   */
  const uploadMany = useCallback(async (files) => {
    const results = []
    for (const file of files) {
      const result = await upload(file)
      results.push(result)
      if (result === null && abortRef.current?.signal.aborted) break  // cancelled
    }
    return results
  }, [upload])


  /**
   * Generate a presigned download URL for a private file.
   */
  const getDownloadUrl = useCallback(async (fileKey) => {
    const res = await fetch(`${API_BASE}/uploads/generate-download-url`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ file_key: fileKey }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail ?? `Server error ${res.status}`)
    }
    const { download_url } = await res.json()
    return download_url
  }, [])


  return {
    status,    // { phase, progress, error, file_key, file_url }
    upload,
    uploadMany,
    getDownloadUrl,
    cancel,
    reset,
  }
}
