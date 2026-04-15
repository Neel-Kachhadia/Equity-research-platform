/**
 * audioApi.js — Audio Intelligence API helpers
 */

const BASE_URL = import.meta.env.VITE_API_URL || ''

/**
 * analyseTranscript
 * POST /audio/analyse
 */
export async function analyseTranscript({ transcript, company_id, quarter, alpha_result }) {
  const resp = await fetch(`${BASE_URL}/audio/analyse`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transcript, company_id, quarter, alpha_result }),
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err.detail || 'Audio analysis failed')
  }
  return resp.json()
}

/**
 * transcribeAudio
 * POST /audio/transcribe  (multipart/form-data)
 *
 * Uploads an audio Blob/File, runs Groq Whisper transcription, then
 * behavioural analysis. Returns AudioSignalResponse + transcript_text.
 *
 * @param {File|Blob} audioFile
 * @param {string|null} companyId
 * @param {string|null} quarter
 * @param {AbortSignal|null} signal  — optional abort controller signal
 */
export async function transcribeAudio(audioFile, companyId = null, quarter = null, signal = null) {
  const form = new FormData()
  // Ensure a proper filename so the backend can detect the format
  const filename = audioFile.name || `recording.${_blobExt(audioFile)}`
  form.append('file', audioFile, filename)
  if (companyId) form.append('company_id', companyId)
  if (quarter)   form.append('quarter',    quarter)

  const resp = await fetch(`${BASE_URL}/audio/transcribe`, {
    method: 'POST',
    body:   form,
    signal,
  })
  if (!resp.ok) {
    let msg = 'Transcription failed'
    try { const j = await resp.json(); msg = j.detail || msg } catch { /* ignore */ }
    throw new Error(msg)
  }
  return resp.json()
}

/** Infer a file extension from a Blob's MIME type. */
function _blobExt(blob) {
  const mime = blob?.type || ''
  if (mime.includes('webm'))  return 'webm'
  if (mime.includes('ogg'))   return 'ogg'
  if (mime.includes('mp4'))   return 'mp4'
  if (mime.includes('wav'))   return 'wav'
  if (mime.includes('mpeg') || mime.includes('mp3')) return 'mp3'
  return 'webm'
}

/**
 * getAudioScorecard
 * POST /audio/scorecard
 */
export async function getAudioScorecard({ transcript, company_id }) {
  const resp = await fetch(`${BASE_URL}/audio/scorecard`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transcript, company_id }),
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err.detail || 'Scorecard generation failed')
  }
  return resp.json()
}
