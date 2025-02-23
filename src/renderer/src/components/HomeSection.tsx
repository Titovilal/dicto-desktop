import { Profile } from '@/types/types'
import { ChevronDown, Columns, FileText, FileCheck } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'
import { StoreSchema } from '@/types/types'
import { CompactMode } from './CompactMode'

// New component for Recording Button
function RecordingButton({
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
      className={`relative flex w-48 justify-center items-center gap-2 py-3 rounded-xl font-medium transition-all duration-300 ${
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
        className={`w-3 h-3 rounded-full transition-all duration-300 ${
          isRecording
            ? 'bg-red-500 animate-pulse'
            : isProcessing
              ? 'bg-yellow-500 animate-pulse'
              : 'bg-emerald-500'
        }`}
      />
      <span className="text-sm">
        {isRecording ? 'Stop Recording' : isProcessing ? 'Processing...' : 'Start Recording'}
      </span>
    </button>
  )
}

// New component for View Selector
function ViewSelector({
  viewMode,
  setViewMode
}: {
  viewMode: 'dual' | 'transcription' | 'processed'
  setViewMode: (mode: 'dual' | 'transcription' | 'processed') => void
}) {
  return (
    <div className="flex bg-zinc-800/30 rounded-xl p-1.5 gap-1.5">
      <button
        onClick={() => setViewMode('dual')}
        className={`p-2 rounded-lg transition-all ${
          viewMode === 'dual' ? 'bg-zinc-700/80 text-zinc-100' : 'text-zinc-400 hover:text-zinc-200'
        }`}
        title="Dual View"
      >
        <Columns className="w-4 h-4" />
      </button>
      <button
        onClick={() => setViewMode('transcription')}
        className={`p-2 rounded-lg transition-all ${
          viewMode === 'transcription'
            ? 'bg-zinc-700/80 text-zinc-100'
            : 'text-zinc-400 hover:text-zinc-200'
        }`}
        title="Transcription"
      >
        <FileText className="w-4 h-4" />
      </button>
      <button
        onClick={() => setViewMode('processed')}
        className={`p-2 rounded-lg transition-all ${
          viewMode === 'processed'
            ? 'bg-zinc-700/80 text-zinc-100'
            : 'text-zinc-400 hover:text-zinc-200'
        }`}
        title="Processed"
      >
        <FileCheck className="w-4 h-4" />
      </button>
    </div>
  )
}

// New component for Profile Selector
function ProfileSelector({
  profiles,
  onSelectProfile,
  selectedProfileName
}: {
  profiles: Profile[]
  onSelectProfile: (profile: Profile) => Promise<void>
  selectedProfileName: string
}) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleProfileChange = (profileName: string) => {
    const profile = profiles.find((p) => p.name === profileName)
    if (profile) {
      onSelectProfile(profile)
    }
  }

  return (
    <div className="relative flex-1" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 rounded-xl bg-zinc-800/30 text-zinc-100 text-sm font-medium focus:outline-none focus:ring-1 focus:ring-zinc-600 flex justify-between items-center transition-all duration-200 hover:bg-zinc-800/50"
      >
        <span className="text-zinc-300">
          {profiles.find((p) => p.name === selectedProfileName)?.name}
        </span>
        <ChevronDown
          className={`w-4 h-4 text-zinc-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {isOpen && (
        <div className="absolute w-full mt-2 py-1 bg-zinc-800/95 backdrop-blur-sm rounded-xl border border-zinc-700/30 shadow-lg z-10">
          {profiles.map((profile) => (
            <button
              key={profile.name}
              className="w-full px-4 py-2.5 text-left text-zinc-300 text-sm hover:bg-zinc-700/50 transition-colors"
              onClick={() => {
                handleProfileChange(profile.name)
                setIsOpen(false)
              }}
            >
              {profile.name}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// Type definition for HomeSectionProps
interface HomeSectionProps {
  isRecording: boolean
  onToggleRecording: () => void
  transcription: string
  processedText: string
  profiles: Profile[]
  isProcessing: boolean
  onSelectProfile: (profile: Profile) => Promise<void>
  settings: StoreSchema['settings'] | null
  isCompactMode: boolean
  onExitCompactMode: () => void
}

// Main component updated to use the new components
export function HomeSection({
  isRecording,
  onToggleRecording,
  transcription,
  processedText,
  profiles,
  isProcessing,
  onSelectProfile,
  settings,
  isCompactMode,
  onExitCompactMode
}: HomeSectionProps) {
  const [isTranscriptionCopied, setIsTranscriptionCopied] = useState(false)
  const [isProcessedCopied, setIsProcessedCopied] = useState(false)
  const [viewMode, setViewMode] = useState<'dual' | 'transcription' | 'processed'>('dual')

  const handleCopy = (text: string, setCopied: (value: boolean) => void) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Early return with warning if no profiles
  if (profiles.length === 0) {
    return (
      <section className="h-full flex flex-col items-center justify-center">
        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-6 max-w-md text-center">
          <h3 className="text-yellow-500 font-medium mb-2">No Profiles Available</h3>
          <p className="text-yellow-500/80 text-sm">
            Please create at least one profile in the Profiles section to start recording.
          </p>
        </div>
      </section>
    )
  }

  // Check for no selected profile
  const selectedProfile = profiles.find((p) => p.name === settings?.selectedProfile)
  if (!selectedProfile) {
    return (
      <section className="h-full flex flex-col items-center justify-center">
        <div className="bg-orange-500/10 border border-orange-500/20 rounded-xl p-6 max-w-md text-center">
          <h3 className="text-orange-500 font-medium mb-2">No Profile Selected</h3>
          <p className="text-orange-500/80 text-sm">
            Please select one profile in the Profiles section to start recording.
          </p>
        </div>
      </section>
    )
  }

  if (isCompactMode) {
    return (
      <CompactMode
        isRecording={isRecording}
        isProcessing={isProcessing}
        onToggleRecording={onToggleRecording}
        profiles={profiles}
        onSelectProfile={onSelectProfile}
        selectedProfileName={selectedProfile?.name}
        transcription={transcription}
        processedText={processedText}
        onExitCompactMode={onExitCompactMode}
      />
    )
  }

  return (
    <section className="h-full flex flex-col">
      <div className="space-y-6 flex-1 flex flex-col">
        <div className="flex items-center gap-4">
          <RecordingButton
            isRecording={isRecording}
            isProcessing={isProcessing}
            onToggleRecording={onToggleRecording}
          />
          <ViewSelector viewMode={viewMode} setViewMode={setViewMode} />
          <ProfileSelector
            profiles={profiles}
            onSelectProfile={onSelectProfile}
            selectedProfileName={selectedProfile?.name}
          />
        </div>

        <div className="space-y-6 flex-1 flex flex-col min-h-0">
          {(viewMode === 'dual' || viewMode === 'transcription') && (
            <div className="flex-1 flex flex-col">
              <div className="flex justify-between items-center mb-2">
                <label className="font-medium text-zinc-400 text-sm flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  Transcription
                </label>
                <button
                  onClick={() => handleCopy(transcription, setIsTranscriptionCopied)}
                  className={`px-3 py-1 text-sm transition-all duration-200 ${
                    isTranscriptionCopied ? 'text-emerald-500' : 'text-zinc-500 hover:text-zinc-300'
                  }`}
                >
                  {isTranscriptionCopied ? 'Copied!' : 'Copy'}
                </button>
              </div>
              <textarea
                className="w-full flex-1 p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50 text-zinc-100 focus:outline-none focus:ring-1 focus:ring-zinc-600 transition-all duration-200 resize-none"
                value={transcription}
                readOnly
              />
            </div>
          )}

          {(viewMode === 'dual' || viewMode === 'processed') && (
            <div className="flex-1 flex flex-col">
              <div className="flex justify-between items-center mb-2">
                <label className="font-medium text-zinc-400 text-sm flex items-center gap-2">
                  <FileCheck className="w-4 h-4" />
                  Processed Text
                </label>
                <button
                  onClick={() => handleCopy(processedText, setIsProcessedCopied)}
                  className={`px-3 py-1 text-sm transition-all duration-200 ${
                    isProcessedCopied ? 'text-emerald-500' : 'text-zinc-500 hover:text-zinc-300'
                  }`}
                >
                  {isProcessedCopied ? 'Copied!' : 'Copy'}
                </button>
              </div>
              <textarea
                className="w-full flex-1 p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50 text-zinc-100 focus:outline-none focus:ring-1 focus:ring-zinc-600 transition-all duration-200 resize-none"
                value={processedText}
                readOnly
              />
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
