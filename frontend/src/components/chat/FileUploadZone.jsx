// src/components/chat/FileUploadZone.jsx
import { useState, useRef } from 'react'
import { Upload } from 'lucide-react'

export default function FileUploadZone({ onFiles }) {
  const [isDragActive, setIsDragActive] = useState(false)
  const inputRef = useRef(null)

  function handleDrop(e) {
    e.preventDefault()
    setIsDragActive(false)
    const files = Array.from(e.dataTransfer.files)
    if (onFiles) onFiles(files)
  }

  function handleFileInput(e) {
    const files = Array.from(e.target.files)
    if (onFiles) onFiles(files)
  }

  return (
    <div
      onDragOver={e => { e.preventDefault(); setIsDragActive(true) }}
      onDragLeave={() => setIsDragActive(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className="max-w-2xl w-full cursor-pointer rounded-xl p-8 text-center transition-all duration-200"
      style={{
        border: `1.5px dashed ${isDragActive ? 'rgba(201,168,76,0.5)' : 'rgba(255,255,255,0.10)'}`,
        background: isDragActive ? 'var(--gold-glow)' : 'transparent',
      }}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,.txt,.json,.csv,.xlsx"
        className="hidden"
        onChange={handleFileInput}
      />

      <Upload
        size={24}
        className={`mx-auto mb-3 transition-colors duration-200 ${isDragActive ? 'text-erebus-gold' : 'text-erebus-text-3'}`}
      />
      <p className="text-[14px] text-erebus-text-2 mb-1">
        {isDragActive ? 'Drop files to upload' : 'Drop annual reports, transcripts, or data files here'}
      </p>
      <p className="text-[12px] font-mono text-erebus-text-3">
        PDF · XLSX · CSV · TXT · JSON — up to 50 MB per file
      </p>
    </div>
  )
}
