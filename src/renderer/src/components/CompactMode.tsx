import { Profile } from '@/types/types'
import {
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  ClipboardCopy,
  Maximize2,
  Mic
} from 'lucide-react'
import { useState } from 'react'
import { sendIPC } from '@/lib/ipc-renderer'

// Mini version of RecordingButton
function CompactRecordingButton({
  isRecording,
  isProcessing,
  onToggleRecording
}: {
  isRecording: boolean
  isProcessing: boolean
  onToggleRecording: () => void
}) {
  return (
    <button
      className={`relative flex items-center justify-center w-12 h-12 rounded-lg font-medium transition-all duration-300 ${
        isRecording
          ? 'bg-red-500/20 text-red-500 hover:bg-red-500/30'
          : isProcessing
            ? 'bg-yellow-500/20 text-yellow-500 cursor-not-allowed opacity-80'
            : 'bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30'
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
      <Mic className="w-5 h-5" />
    </button>
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
    sendIPC('copy-to-clipboard', transcription)
    setIsTranscriptionCopied(true)
    setTimeout(() => setIsTranscriptionCopied(false), 2000)
  }

  const handleCopyProcessed = () => {
    sendIPC('copy-to-clipboard', processedText)
    setIsProcessedCopied(true)
    setTimeout(() => setIsProcessedCopied(false), 2000)
  }

  return (
    <div className="flex items-center gap-3">
      <CompactRecordingButton
        isRecording={isRecording}
        isProcessing={isProcessing}
        onToggleRecording={onToggleRecording}
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
