import { useState } from 'react'
import { Profile } from '@/types/types'
import { LANGUAGES } from '@/lib/languages'
import { useEffect } from 'react'
import { AI_MODELS } from '@/lib/models'
import { AI_MODELS_INFO } from '@/lib/models'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './Select'
import { InfoIcon, HelpCircle } from 'lucide-react'
import { Dialog, DialogContent, DialogTrigger } from './Dialog'
interface ProfileFormProps {
  profile: Profile
  onCancel: () => void
  onSave: (profile: Profile, updates: Profile) => Promise<void>
}

// Componente para la sección de encabezado
function SectionHeader({ title, badge }: { title: string; badge?: string }) {
  return (
    <div className="flex items-center justify-between mb-6">
      <h2 className="text-lg font-medium text-zinc-100">{title}</h2>
      {badge && (
        <div className="px-3 py-1 rounded-full bg-zinc-700/30 text-xs text-zinc-400">{badge}</div>
      )}
    </div>
  )
}

// Componente para campos de texto con descripción
function TextAreaField({
  label,
  value,
  onChange,
  placeholder,
  description,
  rows = 3
}: {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder: string
  description: string
  rows?: number
}) {
  return (
    <div>
      <label className="block text-xs text-zinc-400 mb-2">{label}</label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full p-3 text-sm rounded-lg bg-zinc-800/50 border border-zinc-700/50 text-zinc-100 focus:outline-none focus:ring-1 focus:ring-zinc-600 transition-all duration-200"
        rows={rows}
        placeholder={placeholder}
      />
      <p className="text-xs text-zinc-500">{description}</p>
    </div>
  )
}

// Componente para opciones tipo toggle
function ToggleOption({
  label,
  description,
  checked,
  onChange,
  badge,
  disabled
}: {
  label: string
  description: string
  checked: boolean
  onChange: (checked: boolean) => void
  badge?: string
  disabled?: boolean
}) {
  return (
    <div
      className={`p-4 rounded-lg bg-zinc-800/50 border border-zinc-700/50 ${disabled ? 'opacity-50' : ''}`}
    >
      <label
        className={`flex items-start gap-4 ${disabled ? 'cursor-not-allowed' : 'cursor-pointer'} group`}
      >
        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-sm text-zinc-200 group-hover:text-zinc-100 transition-colors">
              {label}
            </span>
            {badge && (
              <div className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 text-xs">
                {badge}
              </div>
            )}
          </div>
          <p className="text-xs text-zinc-400 group-hover:text-zinc-300 transition-colors">
            {description}
          </p>
        </div>
        <div className="relative flex-shrink-0">
          <input
            type="checkbox"
            checked={checked}
            onChange={(e) => !disabled && onChange(e.target.checked)}
            className="sr-only"
            disabled={disabled}
          />
          <div
            className={`w-10 h-6 rounded-full transition-colors duration-200 ${
              checked && !disabled ? 'bg-emerald-500' : 'bg-zinc-700'
            }`}
          >
            <div
              className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-200 translate-y-1 ${
                checked ? 'translate-x-5' : 'translate-x-1'
              }`}
            />
          </div>
        </div>
      </label>
    </div>
  )
}

// Componente para secciones con fondo gradiente
function Section({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={`p-6 rounded-xl bg-gradient-to-br from-zinc-800/50 to-zinc-800/30 border border-zinc-700/30 backdrop-blur-sm ${className}`}
    >
      {children}
    </div>
  )
}

// Añadir este nuevo componente para el mensaje informativo
function InfoCard() {
  return (
    <div className="mb-4 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-200">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-1">
          <InfoIcon className="w-4 h-4" />
        </div>
        <p className="text-sm leading-relaxed">
          We know there are many options to configure. We're building a playground on our website to
          help you test and improve your prompts. It will be ready soon!
        </p>
      </div>
    </div>
  )
}

// Componente principal ProfileForm
export function ProfileForm({ profile, onCancel, onSave }: ProfileFormProps) {
  const [editingProfile, setEditingProfile] = useState<Profile>(profile)

  useEffect(() => {
    setEditingProfile(profile)
  }, [profile])

  return (
    <div className="flex flex-col h-full">
      {/* Buttons Section */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-sm rounded-md bg-zinc-700/50 text-zinc-300 hover:bg-zinc-700/70 transition-all duration-200"
        >
          Cancel
        </button>
        <button
          onClick={() => onSave(profile, editingProfile)}
          className="px-3 py-1.5 text-sm rounded-md bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30 transition-all duration-200"
        >
          Save Changes
        </button>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto pr-3 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-zinc-800/30 [&::-webkit-scrollbar-thumb]:bg-zinc-600/50 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:border-2 [&::-webkit-scrollbar-thumb]:border-zinc-800/30 hover:[&::-webkit-scrollbar-thumb]:bg-zinc-500/50">
        <div className="space-y-6">
          {/* Info Card */}
          <InfoCard />

          <Section>
            <SectionHeader title="Edit Profile" badge={profile.name} />
            <div className="space-y-6">
              {/* Language Selection */}
              <div>
                <label className="block text-xs text-zinc-400 mb-2">Language</label>
                <Select
                  value={editingProfile.language}
                  onValueChange={(value) =>
                    setEditingProfile({ ...editingProfile, language: value })
                  }
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

              {/* Transcription Prompt */}
              <TextAreaField
                label="Transcription Prompt"
                value={editingProfile.transcriptionPrompt}
                onChange={(value) =>
                  setEditingProfile({ ...editingProfile, transcriptionPrompt: value })
                }
                placeholder="Enter transcription prompt..."
                description="A prompt to guide the transcript's style. You can use it to: improve specific word recognition (e.g., 'NFT, DeFi, DAO'), maintain punctuation, or preserve filler words. The prompt should be in the same language as the audio."
                rows={3}
              />
            </div>
          </Section>

          {/* AI Settings Section */}
          <Section>
            <SectionHeader title="AI Settings" />
            <div className="space-y-6">
              {/* Use AI */}
              <ToggleOption
                label="Use AI"
                description="Process the transcripted text through the selected AI model. It uses the AI prompt and the temperature to process the text."
                checked={editingProfile.useAI}
                onChange={(checked) => setEditingProfile({ ...editingProfile, useAI: checked })}
              />
              {/* Use selected text */}
              <ToggleOption
                label="Use Selected Text"
                description="Use the selected text as context for the AI model. It can be used to rewrite content or just to have more context. Depends on the prompt."
                checked={editingProfile.useSelectedText}
                onChange={(checked) =>
                  setEditingProfile({ ...editingProfile, useSelectedText: checked })
                }
              />

              {/* Model Selection */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <label className="block text-xs text-zinc-400">AI Model</label>
                  <Dialog>
                    <DialogTrigger asChild>
                      <button className="group flex items-center gap-1 px-1.5 py-0.5 rounded-md hover:bg-zinc-800/70 transition-colors">
                        <HelpCircle className="w-4 h-4 text-zinc-500 group-hover:text-zinc-400 transition-colors" />
                        <span className="text-xs text-zinc-500 group-hover:text-zinc-400">
                          Model info
                        </span>
                      </button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl">
                      <div className="space-y-4">
                        <h3 className="text-lg font-medium text-zinc-100">
                          AI Model Recommendations
                        </h3>
                        <div className="space-y-6">
                          {Object.entries(AI_MODELS_INFO).map(([id, info]) => (
                            <div key={id} className="space-y-1.5">
                              <p className="text-sm font-medium text-zinc-200">{info.name}</p>
                              <p className="text-sm text-zinc-400">{info.description}</p>
                              <div className="flex flex-wrap gap-1.5 mt-2">
                                {info.bestFor.map((use, index) => (
                                  <span
                                    key={index}
                                    className="px-2 py-0.5 text-xs rounded-full bg-zinc-800 text-zinc-300 border border-zinc-700/50"
                                  >
                                    {use}
                                  </span>
                                ))}
                              </div>
                              {id !== Object.keys(AI_MODELS_INFO).pop() && (
                                <div className="pt-4 border-b border-zinc-800" />
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>
                <Select
                  value={editingProfile.modelName}
                  onValueChange={(value) =>
                    setEditingProfile({ ...editingProfile, modelName: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a model" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(AI_MODELS).map(([id, name]) => (
                      <SelectItem key={id} value={id}>
                        <div className="flex flex-col">
                          <span>{name}</span>
                          {/* <span className="text-xs text-zinc-400">
                            {AI_MODELS_INFO[id as keyof typeof AI_MODELS].description}
                          </span> */}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="mt-1 text-xs text-zinc-500">
                  Choose the AI model that will process your text. Each model has different
                  capabilities and performance characteristics.
                </p>
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
                  <span>More Accurate</span>
                  <span>More Creative</span>
                </div>
                <p className="mt-1 text-xs text-zinc-500">
                  Controls how creative the AI will be when processing your text. With lower values,
                  the AI will be more conservative and literal. With higher values, the AI will take
                  more creative liberties to improve or transform the text.
                </p>
              </div>

              {/* AI Prompt */}
              <TextAreaField
                label="AI Prompt"
                value={editingProfile.prompt}
                onChange={(value) => setEditingProfile({ ...editingProfile, prompt: value })}
                placeholder="Enter AI prompt..."
                rows={3}
                description="This prompt will be used to process your text. Here are some examples: 'Translate it to python code.', 'Summarize the text.', 'Translate it to spanish.'"
              />
            </div>
          </Section>

          {/* Options Section */}
          <Section>
            <SectionHeader title="Options" />
            <div className="space-y-6">
              <ToggleOption
                label="Copy to Clipboard"
                description="Automatically copy the processed text to your clipboard when ready"
                checked={editingProfile.copyToClipboard}
                onChange={(checked) =>
                  setEditingProfile({
                    ...editingProfile,
                    copyToClipboard: checked,
                    // If copy to clipboard is disabled, auto paste should be disabled too
                    autoPaste: checked ? editingProfile.autoPaste : false,
                    autoEnter: checked ? editingProfile.autoEnter : false
                  })
                }
                badge="Recommended"
              />

              <ToggleOption
                label="Auto Paste"
                description="Automatically paste the transcripted or processed text into the input field when ready. Only available if Copy to Clipboard is enabled."
                checked={editingProfile.autoPaste}
                onChange={(checked) =>
                  setEditingProfile({
                    ...editingProfile,
                    autoPaste: checked,
                    // If auto paste is disabled, auto enter should be disabled too
                    autoEnter: checked ? editingProfile.autoEnter : false
                  })
                }
                disabled={!editingProfile.copyToClipboard}
              />

              <ToggleOption
                label="Auto Enter"
                description="Automatically press enter after the AI processed the text. Only available if Copy to Clipboard and Auto Paste are enabled."
                checked={editingProfile.autoEnter}
                onChange={(checked) => setEditingProfile({ ...editingProfile, autoEnter: checked })}
                disabled={!editingProfile.autoPaste}
              />

              <ToggleOption
                label="Return Both Versions"
                description="Show the transcripted text and the AI processed text in the results. It might be useful to compare the results. If disabled can increase the performance."
                checked={editingProfile.returnBoth}
                onChange={(checked) =>
                  setEditingProfile({ ...editingProfile, returnBoth: checked })
                }
              />
            </div>
          </Section>
        </div>
      </div>
    </div>
  )
}
