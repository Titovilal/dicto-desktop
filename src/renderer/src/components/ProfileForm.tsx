import { useState } from 'react'
import { Profile } from '@/types/types'
import { ChevronDown } from 'lucide-react'
import { LANGUAGES } from '@/lib/languages'
import { LanguageDropdown } from './LanguageDropdown'
import { useRef } from 'react'
import { useEffect } from 'react'
import { AI_MODELS, getModelName } from '@/lib/models'

interface ProfileFormProps {
  profile: Profile
  onCancel: () => void
  onSave: (profile: Profile, updates: Profile) => Promise<void>
}

export function ProfileForm({ profile, onCancel, onSave }: ProfileFormProps) {
  const [editingProfile, setEditingProfile] = useState<Profile>(profile)
  const [isLanguageOpen, setIsLanguageOpen] = useState(false)
  const languageButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    setEditingProfile(profile)
  }, [profile])

  const handleLanguageChange = (key: string) => {
    const updatedProfile = {
      ...editingProfile,
      language: key
    }
    setEditingProfile(updatedProfile)
    setIsLanguageOpen(false)
  }

  return (
    <div className="space-y-6 overflow-y-auto pr-4 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-zinc-800/30 [&::-webkit-scrollbar-thumb]:bg-zinc-600/50 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:border-2 [&::-webkit-scrollbar-thumb]:border-zinc-800/30 hover:[&::-webkit-scrollbar-thumb]:bg-zinc-500/50">
      {/* Header Section */}
      <div className="p-6 rounded-xl bg-gradient-to-br from-zinc-800/50 to-zinc-800/30 border border-zinc-700/30 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-medium text-zinc-100">Edit Profile</h2>
          <div className="px-3 py-1 rounded-full bg-zinc-700/30 text-xs text-zinc-400">
            {profile.name}
          </div>
        </div>

        {/* Prompt Section */}
        <div className="space-y-4">
          <div>
            <label className="block text-xs text-zinc-400 mb-2">Prompt</label>
            <textarea
              value={editingProfile.prompt}
              onChange={(e) => setEditingProfile({ ...editingProfile, prompt: e.target.value })}
              className="w-full p-3 rounded-lg bg-zinc-800/50 border border-zinc-700/50 text-zinc-100 focus:outline-none focus:ring-1 focus:ring-zinc-600 transition-all duration-200"
              rows={3}
              placeholder="Enter your prompt..."
            />
          </div>

          {/* Language Selection */}
          <div>
            <label className="block text-xs text-zinc-400 mb-2">Language</label>
            <div className="relative">
              <button
                ref={languageButtonRef}
                onClick={() => setIsLanguageOpen(!isLanguageOpen)}
                className="w-full px-4 py-3 rounded-lg bg-zinc-800/50 border border-zinc-700/50 text-zinc-100 text-sm font-medium focus:outline-none focus:ring-1 focus:ring-zinc-600 flex justify-between items-center transition-all duration-200 hover:bg-zinc-800/70"
              >
                <span className="text-zinc-300">
                  {LANGUAGES[editingProfile.language] || 'Select Language'}
                </span>
                <ChevronDown
                  className={`w-4 h-4 text-zinc-400 transition-transform duration-200 ${
                    isLanguageOpen ? 'rotate-180' : ''
                  }`}
                />
              </button>

              <LanguageDropdown
                isOpen={isLanguageOpen}
                onClose={() => setIsLanguageOpen(false)}
                selectedLanguage={editingProfile.language}
                onSelectLanguage={handleLanguageChange}
                buttonRef={languageButtonRef}
              />
            </div>
          </div>
        </div>
      </div>

      {/* AI Settings Section */}
      <div className="p-6 rounded-xl bg-gradient-to-br from-zinc-800/50 to-zinc-800/30 border border-zinc-700/30 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-medium text-zinc-100">AI Settings</h2>
        </div>

        <div className="space-y-4">
          {/* Transcription Prompt */}
          <div>
            <label className="block text-xs text-zinc-400 mb-2">Transcription Prompt</label>
            <textarea
              value={editingProfile.transcriptionPrompt}
              onChange={(e) =>
                setEditingProfile({ ...editingProfile, transcriptionPrompt: e.target.value })
              }
              className="w-full p-3 rounded-lg bg-zinc-800/50 border border-zinc-700/50 text-zinc-100 focus:outline-none focus:ring-1 focus:ring-zinc-600 transition-all duration-200"
              rows={2}
              placeholder="Enter transcription prompt..."
            />
          </div>

          {/* Model Selection */}
          <div>
            <label className="block text-xs text-zinc-400 mb-2">AI Model</label>
            <select
              value={editingProfile.modelName}
              onChange={(e) => setEditingProfile({ ...editingProfile, modelName: e.target.value })}
              className="w-full p-3 rounded-lg bg-zinc-800/50 border border-zinc-700/50 text-zinc-100 text-sm font-medium focus:outline-none focus:ring-1 focus:ring-zinc-600 transition-all duration-200"
            >
              {Object.keys(AI_MODELS).map((key) => (
                <option key={key} value={key}>
                  {getModelName(key as keyof typeof AI_MODELS)}
                </option>
              ))}
            </select>
          </div>

          {/* Temperature Slider */}
          <div>
            <label className="block text-xs text-zinc-400 mb-2">
              Temperature: {editingProfile.temperature.toFixed(1)}
            </label>
            <input
              type="range"
              min="0.1"
              max="1"
              step="0.1"
              value={editingProfile.temperature}
              onChange={(e) =>
                setEditingProfile({
                  ...editingProfile,
                  temperature: parseFloat(e.target.value)
                })
              }
              className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-zinc-700/50 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-emerald-500"
            />
            <div className="flex justify-between text-xs text-zinc-500 mt-1">
              <span>More Focused</span>
              <span>More Creative</span>
            </div>
          </div>
        </div>
      </div>

      {/* Options Section */}
      <div className="p-6 rounded-xl bg-gradient-to-br from-zinc-800/50 to-zinc-800/30 border border-zinc-700/30 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-medium text-zinc-100">Options</h2>
        </div>

        <div className="grid grid-cols-1 gap-4">
          <div className="p-4 rounded-lg bg-zinc-800/50 border border-zinc-700/50">
            <label className="flex items-start gap-4 cursor-pointer group">
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-zinc-200 group-hover:text-zinc-100 transition-colors">
                    Use AI
                  </span>
                </div>
                <p className="text-xs text-zinc-400 group-hover:text-zinc-300 transition-colors">
                  Process text through AI to improve grammar, fix typos, and enhance readability
                </p>
              </div>
              <div className="relative flex-shrink-0">
                <input
                  type="checkbox"
                  checked={editingProfile.useAI}
                  onChange={(e) =>
                    setEditingProfile({ ...editingProfile, useAI: e.target.checked })
                  }
                  className="sr-only"
                />
                <div
                  className={`w-10 h-6 rounded-full transition-colors duration-200 ${
                    editingProfile.useAI ? 'bg-emerald-500' : 'bg-zinc-700'
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-200 translate-y-1 ${
                      editingProfile.useAI ? 'translate-x-5' : 'translate-x-1'
                    }`}
                  />
                </div>
              </div>
            </label>
          </div>

          <div className="p-4 rounded-lg bg-zinc-800/50 border border-zinc-700/50">
            <label className="flex items-start gap-4 cursor-pointer group">
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-zinc-200 group-hover:text-zinc-100 transition-colors">
                    Copy to Clipboard
                  </span>
                  <div className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 text-xs">
                    Recommended
                  </div>
                </div>
                <p className="text-xs text-zinc-400 group-hover:text-zinc-300 transition-colors">
                  Automatically copy the processed text to your clipboard when ready
                </p>
              </div>
              <div className="relative flex-shrink-0">
                <input
                  type="checkbox"
                  checked={editingProfile.copyToClipboard}
                  onChange={(e) =>
                    setEditingProfile({ ...editingProfile, copyToClipboard: e.target.checked })
                  }
                  className="sr-only"
                />
                <div
                  className={`w-10 h-6 rounded-full transition-colors duration-200 ${
                    editingProfile.copyToClipboard ? 'bg-emerald-500' : 'bg-zinc-700'
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-200 translate-y-1 ${
                      editingProfile.copyToClipboard ? 'translate-x-5' : 'translate-x-1'
                    }`}
                  />
                </div>
              </div>
            </label>
          </div>

          <div className="p-4 rounded-lg bg-zinc-800/50 border border-zinc-700/50">
            <label className="flex items-start gap-4 cursor-pointer group">
              <div className="flex-1 space-y-1">
                <span className="text-sm text-zinc-200 group-hover:text-zinc-100 transition-colors">
                  Auto Paste
                </span>
                <p className="text-xs text-zinc-400 group-hover:text-zinc-300 transition-colors">
                  Automatically paste the transcripted or processed text into the input field when
                  ready
                </p>
              </div>
              <div className="relative flex-shrink-0">
                <input
                  type="checkbox"
                  checked={editingProfile.autoPaste}
                  onChange={(e) =>
                    setEditingProfile({ ...editingProfile, autoPaste: e.target.checked })
                  }
                  className="sr-only"
                />
                <div
                  className={`w-10 h-6 rounded-full transition-colors duration-200 ${
                    editingProfile.autoPaste ? 'bg-emerald-500' : 'bg-zinc-700'
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-200 translate-y-1 ${
                      editingProfile.autoPaste ? 'translate-x-5' : 'translate-x-1'
                    }`}
                  />
                </div>
              </div>
            </label>
          </div>

          <div className="p-4 rounded-lg bg-zinc-800/50 border border-zinc-700/50">
            <label className="flex items-start gap-4 cursor-pointer group">
              <div className="flex-1 space-y-1">
                <span className="text-sm text-zinc-200 group-hover:text-zinc-100 transition-colors">
                  Return Both Versions
                </span>
                <p className="text-xs text-zinc-400 group-hover:text-zinc-300 transition-colors">
                  Show both the original and processed text in the results
                </p>
              </div>
              <div className="relative flex-shrink-0">
                <input
                  type="checkbox"
                  checked={editingProfile.returnBoth}
                  onChange={(e) =>
                    setEditingProfile({ ...editingProfile, returnBoth: e.target.checked })
                  }
                  className="sr-only"
                />
                <div
                  className={`w-10 h-6 rounded-full transition-colors duration-200 ${
                    editingProfile.returnBoth ? 'bg-emerald-500' : 'bg-zinc-700'
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-200 translate-y-1 ${
                      editingProfile.returnBoth ? 'translate-x-5' : 'translate-x-1'
                    }`}
                  />
                </div>
              </div>
            </label>
          </div>
        </div>
      </div>

      {/* Actions Section */}
      <div className="pb-4">
        <div className="flex items-center justify-between gap-4">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-lg bg-zinc-700/50 text-zinc-300 hover:bg-zinc-700/70 transition-all duration-200"
          >
            Cancel
          </button>
          <button
            onClick={() => onSave(profile, editingProfile)}
            className="px-4 py-2 rounded-lg bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30 transition-all duration-200"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  )
}
