import { Profile } from '@/types/types'
import {
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  ClipboardCopy,
  Maximize2,
  Mic,
  XCircle
} from 'lucide-react'
import { useState, useEffect } from 'react'

// Mini version of RecordingButton with Cancel functionality
function CompactRecordingButton({
  isRecording,
  isProcessing,
  onToggleRecording,
  onCancelRecording
}: {
  isRecording: boolean
  isProcessing: boolean
  onToggleRecording: () => void
  onCancelRecording: () => void
}) {
  const [showCancelButton, setShowCancelButton] = useState(false)

  // Control the appearance of cancel button with a delay
  useEffect(() => {
    let timer: NodeJS.Timeout

    if (isRecording) {
      // Delay showing the cancel button
      timer = setTimeout(() => {
        setShowCancelButton(true)
      }, 300) // Match the transition duration of the record button
    } else {
      setShowCancelButton(false)
    }

    return () => {
      if (timer) clearTimeout(timer)
    }
  }, [isRecording])

  return (
    <div className="flex flex-col gap-1">
      <button
        className={`relative flex items-center justify-center w-12 transition-all duration-300 rounded-lg font-medium ${
          isRecording
            ? 'bg-red-500/20 text-red-500 hover:bg-red-500/30 h-8'
            : isProcessing
              ? 'bg-yellow-500/20 text-yellow-500 cursor-not-allowed opacity-80 h-12'
              : 'bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30 h-12'
        }`}
        onClick={onToggleRecording}
        disabled={isProcessing}
      >
        <div
          className={`w-2 h-2 rounded-full absolute top-2 right-2 transition-all duration-300 ${
            isRecording
              ? 'bg-red-500 animate-pulse'
              : isProcessing
                ? 'bg-yellow-500 animate-pulse'
                : 'bg-emerald-500'
          }`}
        />
        <Mic className={`transition-all duration-300 ${isRecording ? 'w-4 h-4' : 'w-5 h-5'}`} />
      </button>

      {showCancelButton && (
        <button
          className="flex items-center justify-center w-12 h-8 rounded-lg bg-zinc-800/50 text-zinc-400 hover:text-red-400 hover:bg-zinc-800/80 animate-fadeIn"
          onClick={onCancelRecording}
          title="Cancel Recording"
          style={{
            animation: 'fadeIn 0.2s ease-in'
          }}
        >
          <XCircle className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}

// Versión actualizada del selector de perfiles con navegación
function CompactProfileSelector({
  profiles,
  onSelectProfile,
  selectedProfileName
}: {
  profiles: Profile[]
  onSelectProfile: (profile: Profile) => Promise<void>
  selectedProfileName: string
}) {
  const currentIndex = profiles.findIndex((p) => p.name === selectedProfileName)

  const handlePrevProfile = () => {
    const newIndex = currentIndex > 0 ? currentIndex - 1 : profiles.length - 1
    onSelectProfile(profiles[newIndex])
  }

  const handleNextProfile = () => {
    const newIndex = currentIndex < profiles.length - 1 ? currentIndex + 1 : 0
    onSelectProfile(profiles[newIndex])
  }

  return (
    <div className="flex items-center gap-1">
      <button
        onClick={handlePrevProfile}
        className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
      >
        <ChevronLeft className="w-3 h-3" />
      </button>

      <div className="w-full px-2 py-1 rounded-lg bg-zinc-800/30 text-zinc-300 text-xs font-medium min-w-[80px] text-center">
        <span className="truncate block">{selectedProfileName}</span>
      </div>

      <button
        onClick={handleNextProfile}
        className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
      >
        <ChevronRight className="w-3 h-3" />
      </button>
    </div>
  )
}

interface CompactModeProps {
  isRecording: boolean
  isProcessing: boolean
  onToggleRecording: () => void
  onCancelRecording: () => void
  profiles: Profile[]
  onSelectProfile: (profile: Profile) => Promise<void>
  selectedProfileName: string
  transcription: string
  processedText: string
  onExitCompactMode: () => void
}

export function CompactMode({
  isRecording,
  isProcessing,
  onToggleRecording,
  onCancelRecording,
  profiles,
  onSelectProfile,
  selectedProfileName,
  transcription,
  processedText,
  onExitCompactMode
}: CompactModeProps) {
  const [isTranscriptionCopied, setIsTranscriptionCopied] = useState(false)
  const [isProcessedCopied, setIsProcessedCopied] = useState(false)

  const handleCopyTranscription = () => {
    navigator.clipboard.writeText(transcription)
    setIsTranscriptionCopied(true)
    setTimeout(() => setIsTranscriptionCopied(false), 2000)
  }

  const handleCopyProcessed = () => {
    navigator.clipboard.writeText(processedText)
    setIsProcessedCopied(true)
    setTimeout(() => setIsProcessedCopied(false), 2000)
  }

  return (
    <div className="flex items-start gap-3">
      <CompactRecordingButton
        isRecording={isRecording}
        isProcessing={isProcessing}
        onToggleRecording={onToggleRecording}
        onCancelRecording={onCancelRecording}
      />

      <div className="flex flex-col gap-2 flex-1">
        <CompactProfileSelector
          profiles={profiles}
          onSelectProfile={onSelectProfile}
          selectedProfileName={selectedProfileName}
        />

        <div className="flex gap-1.5 w-full">
          <button
            onClick={handleCopyTranscription}
            className="w-full flex gap-2 px-3 py-1.5 rounded-lg bg-zinc-800/30 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 text-xs font-medium"
          >
            {isTranscriptionCopied ? (
              <>
                <ClipboardCheck className="w-4 h-4" />
                Copied!
              </>
            ) : (
              <>
                <ClipboardCopy className="w-4 h-4" />
                Transcription
              </>
            )}
          </button>
          <button
            onClick={handleCopyProcessed}
            className="w-full flex gap-2 px-3 py-1.5 rounded-lg bg-zinc-800/30 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 text-xs font-medium"
          >
            {isProcessedCopied ? (
              <>
                <ClipboardCheck className="w-4 h-4" />
                Copied!
              </>
            ) : (
              <>
                <ClipboardCopy className="w-4 h-4" />
                Processed
              </>
            )}
          </button>
        </div>
      </div>

      <button
        onClick={onExitCompactMode}
        className="p-2.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
        title="Exit Compact Mode"
      >
        <Maximize2 className="w-5 h-5" />
      </button>
    </div>
  )
}
