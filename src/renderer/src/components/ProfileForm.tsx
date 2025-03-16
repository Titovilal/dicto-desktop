import { useState, useEffect, useCallback } from 'react'
import { Profile } from '@/types/types'
import { LANGUAGES } from '@/lib/languages'
import { AI_MODELS, ONLY_LLM_MODELS } from '@/lib/models'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/Select'
import { Zap, Languages, Edit, Clipboard, TriangleAlert } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/Tabs'
import { debounce } from 'lodash'

interface ProfileFormProps {
  profile: Profile
  onCancel: () => void
  onSave: (profile: Profile, updates: Profile) => Promise<void>
}

function TextAreaField({
  label,
  value,
  onChange,
  placeholder,
  description,
  rows = 3,
  disabled = false
}: {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder: string
  description: string
  rows?: number
  disabled?: boolean
}): JSX.Element {
  return (
    <div className={`mb-4 ${disabled ? 'opacity-75' : ''}`}>
      <label className="block text-xs text-zinc-400 mb-1">{label}</label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full p-2 text-sm rounded-lg bg-zinc-800/50 border border-zinc-700/50 text-zinc-100 focus:outline-none focus:ring-1 focus:ring-zinc-600 transition-all duration-200"
        rows={rows}
        placeholder={placeholder}
        disabled={disabled}
      />
      <p className="text-xs text-zinc-500 mt-1">{description}</p>
    </div>
  )
}

function ToggleOption({
  label,
  description,
  checked,
  onChange,
  badge,
  disabled,
  badgeColor
}: {
  label: string
  description: string
  checked: boolean
  onChange: (checked: boolean) => void
  badge?: string
  disabled?: boolean
  badgeColor?: string
}): JSX.Element {
  return (
    <div className={`mb-4 ${disabled ? 'opacity-50' : ''}`}>
      <div className="flex items-center gap-4">
        <div className="relative flex-shrink-0 mt-1">
          <button
            type="button"
            onClick={() => !disabled && onChange(!checked)}
            className={`
              w-11 h-6 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-zinc-900 focus:ring-zinc-600
              ${checked && !disabled ? `bg-emerald-600` : 'bg-zinc-700'}
              ${disabled ? 'cursor-not-allowed' : 'cursor-pointer'}
            `}
            disabled={disabled}
            aria-pressed={checked}
          >
            <span
              className={`
                absolute top-0.5 left-0.5 bg-white w-5 h-5 rounded-full transition-transform duration-200 transform
                ${checked ? 'translate-x-5' : 'translate-x-0'}
                ${checked && !disabled ? 'shadow-emerald-500/30' : ''}
                shadow-md
              `}
            />
          </button>
        </div>

        <label
          className={`flex-1 ${disabled ? 'cursor-not-allowed' : 'cursor-pointer'}`}
          onClick={() => !disabled && onChange(!checked)}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-zinc-200">{label}</span>
            {badge && (
              <div
                className={`px-2 py-0.5 rounded-full bg-${badgeColor}-500/10 text-${badgeColor}-400 text-xs font-medium border border--500/20`}
              >
                {badge}
              </div>
            )}
          </div>
          <p className="text-sm text-zinc-400">{description}</p>
        </label>
      </div>
    </div>
  )
}

export function ProfileForm({ profile, onCancel, onSave }: ProfileFormProps): JSX.Element {
  const [editingProfile, setEditingProfile] = useState<Profile>(profile)

  useEffect(() => {
    setEditingProfile(profile)
  }, [profile])

  const debouncedSave = useCallback(
    debounce(async (currentProfile: Profile) => {
      await onSave(profile, currentProfile)
      console.log('currentProfile', currentProfile)
    }, 1000),
    [profile, onSave]
  )

  const updateProfile = (updates: Partial<Profile>): void => {
    const updatedProfile = { ...editingProfile, ...updates }
    setEditingProfile(updatedProfile)
    debouncedSave(updatedProfile)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-zinc-100">{profile.name} </h1>
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-sm rounded-md bg-zinc-700/50 text-zinc-300 hover:bg-zinc-700/70 transition-all duration-200"
        >
          Go Back
        </button>
      </div>

      <Tabs
        defaultValue={editingProfile.onlyLlm ? 'direct' : 'profile'}
        className="w-full flex flex-col flex-1 overflow-hidden"
      >
        <TabsList className="w-full mb-6 flex-shrink-0">
          <TabsTrigger
            value="direct"
            className="flex-1 text-emerald-800 data-[state=active]:bg-emerald-600/80 data-[state=active]:text-zinc-100"
          >
            Direct LLM
          </TabsTrigger>
          <TabsTrigger value="profile" className="flex-1" disabled={editingProfile.onlyLlm}>
            Profile
          </TabsTrigger>
          <TabsTrigger value="ai" className="flex-1" disabled={editingProfile.onlyLlm}>
            AI Settings
          </TabsTrigger>
          <TabsTrigger value="options" className="flex-1" disabled={editingProfile.onlyLlm}>
            Options
          </TabsTrigger>
        </TabsList>

        <div className="flex-1 overflow-y-auto min-h-0 pr-3 pl-1 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-zinc-800/30 [&::-webkit-scrollbar-thumb]:bg-zinc-600/50 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:border-2 [&::-webkit-scrollbar-thumb]:border-zinc-800/30 hover:[&::-webkit-scrollbar-thumb]:bg-zinc-500/50">
          <TabsContent value="profile" className="mt-0 h-full">
            <div className="space-y-6">
              <div className={editingProfile.onlyLlm ? 'opacity-50 pointer-events-none' : ''}>
                <div className="mb-6">
                  <label className="block text-xs text-zinc-400 mb-1">Language</label>
                  <Select
                    value={editingProfile.language}
                    onValueChange={(value) =>
                      updateProfile({ language: value, modelName: 'gemini-2.0-flash' })
                    }
                    disabled={editingProfile.onlyLlm}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select language" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(LANGUAGES).map(([key, name]) => (
                        <SelectItem key={key} value={key}>
                          {name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="mt-1 text-xs text-zinc-500">
                    The language of the recording. Make sure to select the correct language.
                  </p>
                </div>

                <TextAreaField
                  label="Transcription Prompt"
                  value={editingProfile.transcriptionPrompt}
                  onChange={(value) => updateProfile({ transcriptionPrompt: value })}
                  placeholder="Enter transcription prompt..."
                  description="A prompt to guide the transcript's style. You can use it to: improve specific word recognition (e.g., 'NFT, DeFi, DAO'), maintain punctuation, or preserve filler words."
                  rows={4}
                  disabled={editingProfile.onlyLlm}
                />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="direct" className="mt-0 h-full">
            <div className="space-y-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="relative flex-shrink-0">
                    <button
                      type="button"
                      onClick={() =>
                        updateProfile({
                          onlyLlm: !editingProfile.onlyLlm,
                          modelName: editingProfile.onlyLlm
                            ? 'google/gemini-2.0-flash-001'
                            : 'gemini-2.0-flash'
                        })
                      }
                      className={`
                        w-12 h-7 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-zinc-900 focus:ring-emerald-500
                        ${editingProfile.onlyLlm ? 'bg-emerald-500' : 'bg-zinc-700'}
                      `}
                      aria-pressed={editingProfile.onlyLlm}
                    >
                      <span
                        className={`
                          absolute top-1 left-1 bg-white w-5 h-5 rounded-full transition-transform duration-200 transform
                          ${editingProfile.onlyLlm ? 'translate-x-5' : 'translate-x-0'}
                          ${editingProfile.onlyLlm ? 'shadow-emerald-500/30' : ''}
                          shadow-md
                        `}
                      />
                    </button>
                  </div>
                  <div>
                    <p className="text-base font-semibold text-zinc-200">
                      (Beta) Enable Direct LLM Mode
                    </p>
                    <p className="text-xs text-zinc-400">
                      Skip transcription for faster AI processing
                    </p>
                  </div>
                </div>
              </div>

              <div className={!editingProfile.onlyLlm ? 'opacity-50 pointer-events-none' : ''}>
                <div className="mb-6">
                  <label className="block text-xs text-zinc-400 mb-1">LLM Model</label>
                  <Select
                    value={editingProfile.modelName || 'gemini-2.0-flash'}
                    onValueChange={(value) =>
                      updateProfile({ modelName: value as keyof typeof AI_MODELS })
                    }
                    disabled={!editingProfile.onlyLlm}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(ONLY_LLM_MODELS).map(([key, name]) => (
                        <SelectItem key={key} value={key}>
                          {name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="mt-1 text-xs text-zinc-500">
                    Choose the model for direct LLM processing. Flash is faster, Pro is more
                    capable.
                  </p>
                </div>
              </div>

              <div className="space-y-3 mb-3">
                <div className="flex gap-3">
                  <div className="text-amber-400 flex-shrink-0">
                    <Zap size={18} className="mt-0.5" />
                  </div>
                  <p className="text-sm text-zinc-300">
                    <span className="font-medium">Faster response times</span> - Skip transcription
                    for immediate AI processing
                  </p>
                </div>

                <div className="flex gap-3">
                  <div className="text-blue-400 flex-shrink-0">
                    <Edit size={18} className="mt-0.5" />
                  </div>
                  <p className="text-sm text-zinc-300">
                    <span className="font-medium">Smart text handling</span> - Modify selected text
                    or generate new content using selection as context
                  </p>
                </div>

                <div className="flex gap-3">
                  <div className="text-red-400 flex-shrink-0">
                    <Languages size={18} className="mt-0.5" />
                  </div>
                  <p className="text-sm text-zinc-300">
                    <span className="font-medium">Automatic language detection</span> - Works with
                    any language without configuration
                  </p>
                </div>

                <div className="flex gap-3">
                  <div className="text-green-400 flex-shrink-0">
                    <Clipboard size={18} className="mt-0.5" />
                  </div>
                  <p className="text-sm text-zinc-300">
                    <span className="font-medium">Auto copy & paste</span> - Automatically copies
                    results to clipboard and pastes into active applications
                  </p>
                </div>
              </div>

              <div className="bg-amber-500/15 border border-amber-500/30 rounded-md p-3 mt-6 shadow-inner">
                <div className="flex gap-2 items-start">
                  <div className="text-amber-400 mt-0.5">
                    <TriangleAlert className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm text-zinc-200 font-medium mb-1">Beta Feature</p>
                    <p className="text-sm text-zinc-300">
                      This feature is in beta and may have issues. Please report any problems to{' '}
                      <a
                        href="mailto:terturionsland@gmail.com"
                        className="text-amber-300 underline hover:text-amber-200 transition-colors"
                      >
                        terturionsland@gmail.com
                      </a>{' '}
                      to help us improve it.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="ai" className="mt-0 h-full">
            <div className="space-y-6">
              <div className="space-y-1">
                <ToggleOption
                  label="Use AI"
                  description="Process text through the selected AI model with prompt and temperature"
                  checked={editingProfile.useAI}
                  onChange={(checked) =>
                    updateProfile({
                      useAI: checked,
                      useSelectedText: checked ? editingProfile.useSelectedText : false
                    })
                  }
                />

                <div
                  className={`ml-6 pl-4 border-l-2 ${editingProfile.useAI ? 'border-emerald-600/30' : 'border-zinc-700/50'}`}
                >
                  <ToggleOption
                    label="Use Selected Text"
                    description="Use selected text as context for the AI model"
                    checked={editingProfile.useSelectedText}
                    onChange={(checked) => updateProfile({ useSelectedText: checked })}
                    disabled={!editingProfile.useAI}
                  />
                </div>
              </div>

              <div
                className={`space-y-6 ${!editingProfile.useAI ? 'opacity-50 pointer-events-none' : ''}`}
              >
                <div className="mb-6">
                  <div className="flex items-center gap-2 mb-1">
                    <label className="block text-xs text-zinc-400">AI Model</label>
                  </div>

                  <Select
                    value={editingProfile.modelName}
                    onValueChange={(value) =>
                      updateProfile({ modelName: value as keyof typeof AI_MODELS })
                    }
                    disabled={!editingProfile.useAI}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a model" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(AI_MODELS).map(([id, name]) => (
                        <SelectItem key={id} value={id}>
                          {name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="mt-1 text-xs text-zinc-500">
                    Choose the AI model that will process your text. Each model has different
                    capabilities.
                  </p>
                </div>

                <div className="mb-6">
                  <label className="block text-xs text-zinc-400 mb-1">
                    Temperature: {editingProfile.temperature.toFixed(1)}
                  </label>
                  <input
                    type="range"
                    min="0.1"
                    max="1"
                    step="0.1"
                    value={editingProfile.temperature}
                    onChange={(e) =>
                      updateProfile({
                        temperature: parseFloat(e.target.value)
                      })
                    }
                    disabled={!editingProfile.useAI}
                    className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-zinc-700/50 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-emerald-500"
                  />
                  <div className="flex justify-between text-xs text-zinc-500 mt-1">
                    <span>More Accurate</span>
                    <span>More Creative</span>
                  </div>
                  <p className="mt-1 text-xs text-zinc-500">
                    Controls how creative the AI will be. Lower values are more conservative and
                    literal.
                  </p>
                </div>

                <TextAreaField
                  label="AI Prompt"
                  value={editingProfile.prompt}
                  onChange={(value) => updateProfile({ prompt: value })}
                  placeholder="Enter AI prompt..."
                  rows={4}
                  description="This prompt will be used to process your text. Examples: 'Translate to Python code', 'Summarize', 'Translate to Spanish'"
                  disabled={!editingProfile.useAI}
                />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="options" className="mt-0 h-full">
            <div className="space-y-6">
              <div className="space-y-1">
                <ToggleOption
                  label="Copy to Clipboard"
                  description="Automatically copy the processed text to your clipboard when ready"
                  checked={editingProfile.copyToClipboard}
                  onChange={(checked) =>
                    updateProfile({
                      copyToClipboard: checked,
                      autoPaste: checked ? editingProfile.autoPaste : false,
                      autoEnter: checked ? editingProfile.autoEnter : false
                    })
                  }
                />

                <div
                  className={`ml-6 pl-4 border-l-2 ${editingProfile.copyToClipboard ? 'border-emerald-600/30' : 'border-zinc-700/50'}`}
                >
                  <ToggleOption
                    label="Auto Paste"
                    description="Automatically paste the text into the input field when ready"
                    checked={editingProfile.autoPaste}
                    onChange={(checked) =>
                      updateProfile({
                        autoPaste: checked,
                        autoEnter: checked ? editingProfile.autoEnter : false
                      })
                    }
                    disabled={!editingProfile.copyToClipboard}
                    badge="Recommended"
                    badgeColor="emerald"
                  />

                  <div
                    className={`ml-6 pl-4 border-l-2 ${editingProfile.autoPaste && editingProfile.copyToClipboard ? 'border-emerald-600/30' : 'border-zinc-700/50'}`}
                  >
                    <ToggleOption
                      label="Auto Enter"
                      description="Automatically press enter after the AI processed the text"
                      checked={editingProfile.autoEnter}
                      onChange={(checked) => updateProfile({ autoEnter: checked })}
                      disabled={!editingProfile.autoPaste || !editingProfile.copyToClipboard}
                      badge="Useful for chat or search"
                      badgeColor="blue"
                    />
                  </div>
                </div>

                <ToggleOption
                  label="Return Both Versions"
                  description="Show both transcripted and AI processed text in the results."
                  checked={editingProfile.returnBoth}
                  onChange={(checked) => updateProfile({ returnBoth: checked })}
                  badge="Only for debugging"
                  badgeColor="zinc"
                />
              </div>
            </div>
          </TabsContent>
        </div>
      </Tabs>
    </div>
  )
}

export default ProfileForm
