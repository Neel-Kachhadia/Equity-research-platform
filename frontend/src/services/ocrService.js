/**
 * src/services/ocrService.js
 *
 * Thin API layer for the OCR pipeline.
 * All fetch calls go through here — components stay clean.
 */

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function _json(res) {
  if (!res.ok) {
    let detail = `Server returned ${res.status}`
    try {
      const body = await res.json()
      detail = body.detail ?? body.message ?? detail
    } catch {}
    throw new Error(detail)
  }
  return res.json()
}

/**
 * Register an already-uploaded S3 file for OCR.
 * @param {string} fileName   Original file name
 * @param {string} s3Key      S3 object key (from presigned upload result)
 * @param {string} mimeType   MIME type
 * @param {number} fileSize   File size in bytes
 * @returns {Promise<Object>} OcrDocumentResponse
 */
export async function registerDocument(fileName, s3Key, mimeType, fileSize) {
  const res = await fetch(`${API_BASE}/ocr/register`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({
      file_name: fileName,
      s3_key:    s3Key,
      mime_type: mimeType,
      file_size: fileSize ?? null,
    }),
  })
  return _json(res)
}

/**
 * Start OCR processing for a registered document.
 * Returns 202 immediately — poll getDocument() for status.
 * @param {number} documentId
 * @returns {Promise<Object>} OcrProcessResponse
 */
export async function processDocument(documentId) {
  const res = await fetch(`${API_BASE}/ocr/${documentId}/process`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
  })
  return _json(res)
}

/**
 * Get document metadata + current status.
 * @param {number} documentId
 * @returns {Promise<Object>} OcrDocumentResponse
 */
export async function getDocument(documentId) {
  const res = await fetch(`${API_BASE}/ocr/${documentId}`)
  return _json(res)
}

/**
 * Get extracted OCR text and per-page breakdown.
 * Only call when status === 'completed'.
 * @param {number} documentId
 * @returns {Promise<Object>} OcrResultResponse
 */
export async function getResult(documentId) {
  const res = await fetch(`${API_BASE}/ocr/${documentId}/result`)
  return _json(res)
}

/**
 * List OCR document history with pagination.
 * @param {number} page   1-indexed
 * @param {number} limit  Results per page
 * @returns {Promise<Object>} OcrHistoryResponse
 */
export async function listHistory(page = 1, limit = 20) {
  const res = await fetch(`${API_BASE}/ocr/history?page=${page}&limit=${limit}`)
  return _json(res)
}

/**
 * Run LLM analysis (Groq) on the OCR-extracted text of a completed document.
 * @param {number} documentId
 * @returns {Promise<Object>} { document_id, file_name, provider, analysis }
 */
export async function analyzeDocument(documentId) {
  const res = await fetch(
    `${API_BASE}/ocr/${documentId}/analyze`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' } },
  )
  return _json(res)
}
