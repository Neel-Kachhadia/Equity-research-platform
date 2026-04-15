import { useState, useRef, useEffect, useCallback } from 'react'
import { analyseTranscript, transcribeAudio } from '../../services/audioApi'
import { fetchCompanies } from '../../services/api'

// ── Colour helpers ─────────────────────────────────────────────────────────────
const SENTIMENT_COLORS = {
  positive: { text: '#2ECC8A', bg: '#2ECC8A12', border: '#2ECC8A44', label: 'Positive' },
  neutral:  { text: '#C9A84C', bg: '#C9A84C12', border: '#C9A84C44', label: 'Neutral'  },
  negative: { text: '#D95555', bg: '#D9555512', border: '#D9555544', label: 'Negative' },
}
const HESITATION_COLORS = {
  Low:      { text: '#2ECC8A', bar: '#2ECC8A' },
  Moderate: { text: '#C9A84C', bar: '#C9A84C' },
  High:     { text: '#D95555', bar: '#D95555' },
}

// ── Animated gauge ─────────────────────────────────────────────────────────────
function HesitationBar({ score, label }) {
  const [width, setWidth] = useState(0)
  const color = HESITATION_COLORS[label] || HESITATION_COLORS.Moderate
  const pct   = Math.min(100, Math.round(score * 100))

  useEffect(() => {
    const t = setTimeout(() => setWidth(pct), 120)
    return () => clearTimeout(t)
  }, [pct])

  return (
    <div>
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-widest">Hesitation Score</span>
        <span className="text-[13px] font-mono font-bold" style={{ color: color.text }}>
          {label} · {pct}%
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{ width: `${width}%`, background: color.bar, boxShadow: `0 0 8px ${color.bar}55` }}
        />
      </div>
      <div className="flex justify-between mt-1">
        <span className="text-[10px] font-mono text-erebus-text-3">0%</span>
        <span className="text-[10px] font-mono text-erebus-text-3">50%</span>
      </div>
    </div>
  )
}

// ── Sentiment ring ─────────────────────────────────────────────────────────────
function SentimentRing({ label, score }) {
  const [animated, setAnimated] = useState(false)
  const c = SENTIMENT_COLORS[label] || SENTIMENT_COLORS.neutral
  const r = 38, cx = 50, cy = 50
  const circ = 2 * Math.PI * r
  const pct  = label === 'positive' ? score : label === 'negative' ? 1 - score : 0.5
  const dash  = animated ? pct * circ : 0

  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 200)
    return () => clearTimeout(t)
  }, [label])

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative w-28 h-28">
        <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
          <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
          <circle
            cx={cx} cy={cy} r={r} fill="none"
            stroke={c.text} strokeWidth="8"
            strokeDasharray={`${circ}`}
            strokeDashoffset={circ - dash}
            strokeLinecap="round"
            style={{
              transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4,0,0.2,1)',
              filter: `drop-shadow(0 0 6px ${c.text}88)`,
            }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-[22px] font-bold font-mono" style={{ color: c.text }}>
            {Math.round(score * 100)}%
          </span>
        </div>
      </div>
      <div
        className="px-3 py-1 rounded-full text-[11px] font-mono font-semibold border"
        style={{ color: c.text, borderColor: c.border, background: c.bg }}
      >
        {c.label}
      </div>
    </div>
  )
}

// ── Signal card ────────────────────────────────────────────────────────────────
function SignalCard({ icon, label, value, sub, color }) {
  return (
    <div className="rounded-xl bg-erebus-surface border border-white/[0.07] p-4 flex flex-col gap-1.5">
      <div className="flex items-center gap-2 text-erebus-text-3 text-[11px] font-mono uppercase tracking-widest">
        <span>{icon}</span>
        <span>{label}</span>
      </div>
      <div className="text-[20px] font-bold font-mono" style={{ color: color || '#E8D5A3' }}>
        {value}
      </div>
      {sub && <div className="text-[11px] font-mono text-erebus-text-3">{sub}</div>}
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────────
export default function AudioIntelligencePage() {
  const [transcript, setTranscript] = useState('')
  const [companyId,  setCompanyId]  = useState('')
  const [quarter,    setQuarter]    = useState('')
  const [loading,    setLoading]    = useState(false)
  const [result,     setResult]     = useState(null)
  const [error,      setError]      = useState(null)
  const [stage,      setStage]      = useState(0)
  const resultRef = useRef(null)

  // ── Audio input state ──────────────────────────────────────────────────────
  const [audioTab,    setAudioTab]    = useState('paste')   // 'paste' | 'upload' | 'record'
  const [audioStatus, setAudioStatus] = useState('idle')    // 'idle' | 'recording' | 'transcribing' | 'done'
  const [audioError,  setAudioError]  = useState(null)
  const [audioNote,   setAudioNote]   = useState(null)
  const [isDragging,  setIsDragging]  = useState(false)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef   = useRef([])
  const abortCtrlRef     = useRef(null)
  const fileInputRef     = useRef(null)

  // S3 company universe for the company picker
  const [universe, setUniverse] = useState([])
  useEffect(() => {
    fetchCompanies()
      .then(d => setUniverse(d.companies || []))
      .catch(() => {}) // silently degrade — user can still type
  }, [])

  const STAGES = ['Classifying speakers…', 'Analysing sentiment…', 'Detecting hesitation…', 'Generating signal…']

  useEffect(() => {
    if (!loading) return
    const t = setInterval(() => setStage(s => (s + 1) % STAGES.length), 1600)
    return () => clearInterval(t)
  }, [loading])

  // ── Audio: shared handler after transcription finishes ────────────────────
  const onTranscriptionDone = useCallback((data) => {
    if (data.transcript_text) {
      setTranscript(data.transcript_text)
      setAudioNote('✓ Audio transcribed — transcript populated below')
    }
    if (data.segments_analysed != null) {
      setResult(data)
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 150)
    }
    setAudioStatus('done')
    setAudioTab('paste')
  }, [])

  // ── Audio: file upload ─────────────────────────────────────────────────────
  const handleFileUpload = useCallback(async (file) => {
    const okExt = ['mp3','wav','m4a','ogg','webm','flac','mp4']
    const ext = file.name?.split('.').pop()?.toLowerCase() || ''
    if (!okExt.includes(ext)) {
      setAudioError('Unsupported format. Use MP3, WAV, M4A, OGG, WebM or FLAC.')
      return
    }
    if (file.size > 25 * 1024 * 1024) {
      setAudioError('File too large (max 25 MB).')
      return
    }
    setAudioError(null)
    setAudioNote(null)
    setAudioStatus('transcribing')
    abortCtrlRef.current = new AbortController()
    try {
      const data = await transcribeAudio(file, companyId || null, quarter || null, abortCtrlRef.current.signal)
      onTranscriptionDone(data)
    } catch (e) {
      if (e.name !== 'AbortError') setAudioError(e.message || 'Transcription failed')
      setAudioStatus('idle')
    }
  }, [companyId, quarter, onTranscriptionDone])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) handleFileUpload(file)
  }, [handleFileUpload])

  // ── Audio: microphone recording ────────────────────────────────────────────
  const startRecording = useCallback(async () => {
    setAudioError(null)
    setAudioNote(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      audioChunksRef.current = []
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' })
      mr.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data) }
      mr.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        setAudioStatus('transcribing')
        abortCtrlRef.current = new AbortController()
        try {
          const data = await transcribeAudio(blob, companyId || null, quarter || null, abortCtrlRef.current.signal)
          onTranscriptionDone(data)
        } catch (e) {
          if (e.name !== 'AbortError') setAudioError(e.message || 'Transcription failed')
          setAudioStatus('idle')
        }
      }
      mr.start()
      mediaRecorderRef.current = mr
      setAudioStatus('recording')
    } catch {
      setAudioError('Microphone access denied. Please allow mic permissions and retry.')
    }
  }, [companyId, quarter, onTranscriptionDone])

  const stopRecording  = useCallback(() => { mediaRecorderRef.current?.stop() }, [])
  const cancelAudio    = useCallback(() => {
    mediaRecorderRef.current?.stop()
    abortCtrlRef.current?.abort()
    setAudioStatus('idle')
  }, [])

  // ── Transcript analysis ────────────────────────────────────────────────────
  const handleAnalyse = async () => {
    if (!transcript.trim() || transcript.trim().split(/\s+/).length < 30) {
      setError('Please paste a transcript of at least 30 words.')
      return
    }
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      const data = await analyseTranscript({
        transcript,
        company_id: companyId || undefined,
        quarter:    quarter   || undefined,
      })
      setResult(data)
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100)
    } catch (e) {
      setError(e.message || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setTranscript('')
    setCompanyId('')
    setQuarter('')
    setResult(null)
    setError(null)
    setAudioNote(null)
    setAudioError(null)
    setAudioStatus('idle')
  }

  const SAMPLE = `[speaker_0] Good morning everyone. I am pleased to report that TCS delivered strong revenue growth of 8 percent year on year in Q3 FY25. Our margins remain robust at 24.5 percent and we are highly confident in our strategic direction.

[speaker_0] We expect continued momentum in financial services and retail verticals going forward. We believe our investments in AI and cloud will drive long-term value creation for our shareholders.

[speaker_1] Thank you. Can you elaborate on the headwinds you mentioned last quarter? Is the uncertainty around discretionary spending still a concern?

[speaker_0] Yes, we might see some pressure in the near term. Um, you know, clients are being cautious with discretionary budgets. We expect this to stabilize in the coming quarters but it could take some time.

[speaker_1] And what about margins? The guidance was 25 percent but you delivered 24.5?

[speaker_0] Well, approximately we are in line with our expectations. There may be some variability depending on the deal mix. We remain cautiously optimistic about the second half.`

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-erebus-bg text-erebus-text-1 px-6 py-8 max-w-5xl mx-auto">

      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-9 h-9 rounded-xl bg-erebus-gold/10 border border-erebus-gold/30 flex items-center justify-center text-lg">
            🎤
          </div>
          <div>
            <h1 className="text-2xl font-bold text-erebus-text-1 font-serif tracking-tight">
              Audio Intelligence
            </h1>
            <p className="text-[12px] font-mono text-erebus-text-3 mt-0.5">
              Earnings Call Behavioral Signal Analysis
            </p>
          </div>
        </div>
        <p className="text-[13px] text-erebus-text-2 leading-relaxed max-w-2xl">
          Upload an audio file, record live, or paste a transcript to extract management credibility
          signals — sentiment, hesitation patterns, hedge language density, and tone consistency — powered by Groq Whisper.
        </p>
      </div>

      {/* Input panel */}
      <div className="rounded-2xl border border-white/[0.08] bg-erebus-surface overflow-hidden mb-6">

        {/* ── Tab bar ── */}
        <div className="px-5 py-3 border-b border-white/[0.06] flex items-center justify-between">
          <div className="flex gap-1">
            {[
              { id: 'paste',  label: ' Paste Transcript' },
              { id: 'upload', label: ' Upload Audio' },
              { id: 'record', label: ' Record Live' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => { setAudioTab(tab.id); setAudioError(null) }}
                className="px-3 py-1.5 rounded-lg text-[11px] font-mono transition-all"
                style={{
                  background: audioTab === tab.id ? 'rgba(201,168,76,0.15)' : 'transparent',
                  color:      audioTab === tab.id ? '#C9A84C' : '#5E6880',
                  border:     audioTab === tab.id ? '1px solid rgba(201,168,76,0.35)' : '1px solid transparent',
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
          {audioTab === 'paste' && (
            <button
              onClick={() => setTranscript(SAMPLE)}
              className="text-[11px] font-mono text-erebus-gold/70 hover:text-erebus-gold transition-colors"
            >
              Load sample →
            </button>
          )}
        </div>

        {/* ── UPLOAD TAB ── */}
        {audioTab === 'upload' && (
          <div className="px-5 py-6">
            <input
              ref={fileInputRef}
              type="file"
              accept=".mp3,.wav,.m4a,.ogg,.webm,.flac,.mp4,audio/*"
              className="hidden"
              onChange={e => {
                const f = e.target.files?.[0]
                if (f) handleFileUpload(f)
                e.target.value = ''
              }}
            />

            {audioStatus === 'transcribing' ? (
              <div className="flex flex-col items-center gap-4 py-10">
                <div className="w-12 h-12 rounded-full border-2 border-erebus-gold/30 border-t-erebus-gold animate-spin" />
                <p className="text-[13px] font-mono text-erebus-text-2">Transcribing with Groq Whisper…</p>
                <button
                  onClick={cancelAudio}
                  className="text-[11px] font-mono text-erebus-text-3 hover:text-erebus-text-2 transition-colors"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <div
                onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed rounded-xl flex flex-col items-center gap-3 py-14 cursor-pointer transition-all duration-200"
                style={{
                  borderColor: isDragging ? '#C9A84C' : 'rgba(255,255,255,0.12)',
                  background:  isDragging ? 'rgba(201,168,76,0.05)' : 'rgba(255,255,255,0.02)',
                }}
              >
                <span className="text-5xl">{isDragging ? '🎧' : '📁'}</span>
                <div className="text-center">
                  <p className="text-[14px] font-mono text-erebus-text-1 mb-1">
                    {isDragging ? 'Drop to transcribe' : 'Drop audio file here'}
                  </p>
                  <p className="text-[11px] font-mono text-erebus-text-3">or click to browse</p>
                </div>
                <div className="flex gap-2 mt-1 flex-wrap justify-center">
                  {['MP3','WAV','M4A','OGG','WebM','FLAC'].map(f => (
                    <span key={f} className="px-2 py-0.5 rounded text-[9px] font-mono bg-white/[0.06] text-erebus-text-3">{f}</span>
                  ))}
                </div>
                <p className="text-[10px] font-mono text-erebus-text-3/60">Max 25 MB · Powered by Groq Whisper</p>
              </div>
            )}

            {audioError && (
              <div className="mt-3 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-[12px] font-mono text-red-400">
                ⚠ {audioError}
              </div>
            )}
          </div>
        )}

        {/* ── RECORD TAB ── */}
        {audioTab === 'record' && (
          <div className="px-5 py-10 flex flex-col items-center gap-6">
            {audioStatus === 'transcribing' ? (
              <>
                <div className="w-14 h-14 rounded-full border-2 border-erebus-gold/30 border-t-erebus-gold animate-spin" />
                <p className="text-[13px] font-mono text-erebus-text-2">Transcribing with Groq Whisper…</p>
                <button onClick={cancelAudio} className="text-[11px] font-mono text-erebus-text-3 hover:text-erebus-text-2 transition-colors">Cancel</button>
              </>
            ) : audioStatus === 'recording' ? (
              <>
                <div className="relative">
                  <div className="absolute -inset-3 rounded-full bg-red-500/20 animate-ping" />
                  <button
                    onClick={stopRecording}
                    className="relative w-20 h-20 rounded-full bg-red-500 hover:bg-red-400 transition-colors flex items-center justify-center text-3xl shadow-lg shadow-red-500/40"
                  >
                    ⏹
                  </button>
                </div>
                <div className="text-center">
                  <p className="text-[15px] font-mono text-red-400 font-semibold">Recording…</p>
                  <p className="text-[11px] font-mono text-erebus-text-3 mt-1">Click the button above to stop</p>
                </div>
              </>
            ) : (
              <>
                <button
                  onClick={startRecording}
                  className="w-20 h-20 rounded-full flex items-center justify-center text-3xl transition-all duration-200 hover:scale-105 active:scale-95"
                  style={{
                    background: 'linear-gradient(135deg,#C9A84C,#E8D5A3)',
                    boxShadow:  '0 0 32px rgba(201,168,76,0.45)',
                  }}
                >
                  🎤
                </button>
                <div className="text-center">
                  <p className="text-[14px] font-mono text-erebus-text-1">Click to start recording</p>
                  <p className="text-[11px] font-mono text-erebus-text-3 mt-1">Speak your earnings call transcript — Groq Whisper will transcribe it instantly</p>
                </div>
              </>
            )}

            {audioError && (
              <div className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-[12px] font-mono text-red-400 text-center max-w-sm">
                ⚠ {audioError}
              </div>
            )}
          </div>
        )}

        {/* ── Success banner (all tabs) ── */}
        {audioNote && (
          <div className="mx-5 mb-1 px-4 py-2.5 rounded-xl bg-green-500/10 border border-green-500/30 text-[12px] font-mono text-green-400 flex items-center gap-2">
            <span>✓</span> {audioNote}
          </div>
        )}

        {/* ── Meta fields (company / quarter) ── */}
        <div className="px-5 pt-4 pb-2 flex gap-4">
          <div className="flex-1">
            <label className="block text-[10px] font-mono text-erebus-text-3 uppercase tracking-widest mb-1.5">
              Company (optional)
            </label>
            <input
              id="audio-company-input"
              type="text"
              list="audio-company-list"
              placeholder={universe.length ? `e.g. ${universe[0]?.ticker || 'TCS'}` : 'e.g. TCS'}
              value={companyId}
              onChange={e => setCompanyId(e.target.value.toUpperCase())}
              className="w-full bg-white/[0.04] border border-white/[0.1] rounded-lg px-3 py-2 text-[13px] font-mono text-erebus-text-1 placeholder-erebus-text-3/50 focus:outline-none focus:border-erebus-gold/40 transition-colors"
            />
            {universe.length > 0 && (
              <datalist id="audio-company-list">
                {universe.map(c => <option key={c.ticker} value={c.ticker} />)}
              </datalist>
            )}
          </div>
          <div className="flex-1">
            <label className="block text-[10px] font-mono text-erebus-text-3 uppercase tracking-widest mb-1.5">
              Quarter (optional)
            </label>
            <input
              id="audio-quarter-input"
              type="text"
              placeholder="e.g. Q3FY25"
              value={quarter}
              onChange={e => setQuarter(e.target.value)}
              className="w-full bg-white/[0.04] border border-white/[0.1] rounded-lg px-3 py-2 text-[13px] font-mono text-erebus-text-1 placeholder-erebus-text-3/50 focus:outline-none focus:border-erebus-gold/40 transition-colors"
            />
          </div>
        </div>

        {/* ── Transcript textarea (paste tab or auto-populated) ── */}
        <div className="px-5 pb-4">
          <label className="block text-[10px] font-mono text-erebus-text-3 uppercase tracking-widest mb-1.5">
            {audioTab === 'paste' ? 'Transcript' : 'Transcript (auto-populated after transcription)'}
          </label>
          <textarea
            id="audio-transcript-textarea"
            rows={10}
            placeholder={`Paste earnings call transcript here…\n\nSupports formats:\n  [speaker_0] text… (Groq Whisper output)\n  Management: text…\n  Q: / A: format\n  Plain text`}
            value={transcript}
            onChange={e => setTranscript(e.target.value)}
            className="w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-4 py-3 text-[13px] font-mono text-erebus-text-1 placeholder-erebus-text-3/40 focus:outline-none focus:border-erebus-gold/40 transition-colors resize-none leading-relaxed"
          />
          <div className="flex items-center justify-between mt-2">
            <span className="text-[10px] font-mono text-erebus-text-3">
              {transcript.trim().split(/\s+/).filter(Boolean).length} words
            </span>
          </div>
        </div>

        {/* ── Action buttons ── */}
        <div className="px-5 pb-5 flex items-center gap-3">
          <button
            id="audio-analyse-btn"
            onClick={handleAnalyse}
            disabled={loading || !transcript.trim()}
            className="flex items-center gap-2.5 px-6 py-2.5 rounded-xl font-mono text-[13px] font-semibold disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200"
            style={{
              background: 'linear-gradient(135deg, #C9A84C 0%, #E8D5A3 100%)',
              color:      '#0A0B0F',
              boxShadow:  loading ? 'none' : '0 0 20px #C9A84C33',
            }}
          >
            {loading ? (
              <>
                <span className="w-3.5 h-3.5 rounded-full border-2 border-black/30 border-t-black animate-spin" />
                {STAGES[stage]}
              </>
            ) : (
              <>
                <span>⚡</span>
                Analyse Transcript
              </>
            )}
          </button>

          {(transcript || result) && (
            <button
              onClick={handleClear}
              className="px-4 py-2.5 rounded-xl font-mono text-[12px] text-erebus-text-3 hover:text-erebus-text-1 border border-white/[0.08] hover:border-white/[0.15] transition-all"
            >
              Clear
            </button>
          )}
        </div>

        {/* ── Error ── */}
        {error && (
          <div className="mx-5 mb-5 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-[12px] font-mono text-red-400">
            ⚠ {error}
          </div>
        )}
      </div>

      {/* ── Capability chips ── */}
      <div className="flex flex-wrap gap-2 mb-8">
        {[
          'No ML model required',
          'Rule-based · Deterministic',
          '&lt; 100ms per segment',
          'Speaker-aware',
          'Groq Whisper STT',
          'α₆ credibility feed',
        ].map(tag => (
          <span key={tag} className="px-3 py-1 rounded-full text-[10px] font-mono bg-white/[0.04] border border-white/[0.08] text-erebus-text-3">
            {tag}
          </span>
        ))}
      </div>

      {/* ── Results ── */}
      {result && (
        <div ref={resultRef} className="space-y-5 animate-[fadeInUp_0.4s_ease-out]">

          {/* Quality + meta strip */}
          <div className="flex items-center gap-3 flex-wrap">
            {result.company_id && (
              <span className="px-3 py-1 rounded-full text-[11px] font-mono bg-erebus-gold/10 border border-erebus-gold/30 text-erebus-gold">
                {result.company_id}{result.quarter ? ` · ${result.quarter}` : ''}
              </span>
            )}
            <span className={`px-3 py-1 rounded-full text-[11px] font-mono border ${
              result.data_quality === 'sufficient'
                ? 'bg-green-500/10 border-green-500/30 text-green-400'
                : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
            }`}>
              {result.data_quality === 'sufficient' ? '✓ Sufficient data' : '⚠ ' + result.data_quality}
            </span>
            <span className="text-[11px] font-mono text-erebus-text-3">
              {result.segments_analysed} segments analysed
            </span>
            {result.transcript_text && (
              <span className="px-3 py-1 rounded-full text-[11px] font-mono bg-blue-500/10 border border-blue-500/30 text-blue-400">
                🎤 From audio
              </span>
            )}
          </div>

          {/* Row 1: Sentiment + Scorecard */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

            {/* Sentiment ring */}
            <div className="rounded-2xl border border-white/[0.08] bg-erebus-surface p-6">
              <h3 className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-widest mb-5">
                Overall Sentiment
              </h3>
              <div className="flex gap-8 items-center">
                <SentimentRing label={result.sentiment} score={result.sentiment_score} />
                <div className="flex flex-col gap-4 flex-1">
                  <div>
                    <p className="text-[10px] font-mono text-erebus-text-3 uppercase tracking-widest mb-1">Management</p>
                    <p className="text-[13px] font-mono font-semibold capitalize" style={{
                      color: SENTIMENT_COLORS[result.management_sentiment]?.text || '#C9A84C'
                    }}>
                      {result.management_sentiment}
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] font-mono text-erebus-text-3 uppercase tracking-widest mb-1">Analyst</p>
                    <p className="text-[13px] font-mono font-semibold capitalize" style={{
                      color: SENTIMENT_COLORS[result.analyst_sentiment]?.text || '#C9A84C'
                    }}>
                      {result.analyst_sentiment}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Scorecard block */}
            <div className="rounded-2xl border border-white/[0.08] bg-erebus-surface p-6">
              <h3 className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-widest mb-5">
                Management Credibility
              </h3>
              <div className="space-y-3">
                {[
                  { label: 'Tone',              value: result.tone_label },
                  { label: 'Uncertainty Trend', value: result.uncertainty_trend },
                  { label: 'Tone Shift',        value: result.tone_shift        ? '⚠ Detected' : '✓ Stable' },
                  { label: 'Hedging Trend',     value: result.increasing_hedging ? '↑ Increasing' : '→ Stable' },
                ].map(({ label, value }) => (
                  <div key={label} className="flex items-center justify-between">
                    <span className="text-[11px] font-mono text-erebus-text-3">{label}</span>
                    <span className="text-[12px] font-mono text-erebus-text-1 font-semibold">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Row 2: Hesitation + Signal cards */}
          <div className="rounded-2xl border border-white/[0.08] bg-erebus-surface p-6">
            <h3 className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-widest mb-5">
              Hesitation Analysis
            </h3>
            <HesitationBar score={result.hesitation_score} label={result.hesitation_label} />
            <div className="grid grid-cols-2 gap-4 mt-5">
              <SignalCard
                icon="🔤" label="Filler Rate"
                value={`${(result.filler_rate * 100).toFixed(1)}%`}
                sub="Filler words / total words"
                color="#C9A84C"
              />
              <SignalCard
                icon="🛡" label="Hedge Rate"
                value={`${(result.hedge_rate * 100).toFixed(1)}%`}
                sub="Hedge phrases / total words"
                color="#4A8FE7"
              />
            </div>
          </div>

          {/* Credibility boost */}
          <div className="rounded-2xl border border-white/[0.08] bg-erebus-surface p-6">
            <h3 className="text-[11px] font-mono text-erebus-text-3 uppercase tracking-widest mb-4">
              α₆ Credibility Boost
            </h3>
            <div className="flex items-center gap-4">
              <span
                className="text-3xl font-bold font-mono"
                style={{ color: result.credibility_boost >= 0 ? '#2ECC8A' : '#D95555' }}
              >
                {result.credibility_boost >= 0 ? '+' : ''}{result.credibility_boost.toFixed(4)}
              </span>
              <p className="text-[12px] font-mono text-erebus-text-3 leading-relaxed max-w-lg">
                {result.interpretation}
              </p>
            </div>
          </div>

          {/* Warnings */}
          {result.warnings?.length > 0 && (
            <div className="rounded-xl bg-amber-500/10 border border-amber-500/30 px-4 py-3">
              <p className="text-[11px] font-mono text-amber-400 font-semibold mb-1">Warnings</p>
              {result.warnings.map((w, i) => (
                <p key={i} className="text-[11px] font-mono text-amber-400/80">⚠ {w}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
