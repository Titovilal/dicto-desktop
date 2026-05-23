import { useState } from 'react'
import { usePresets, Preset } from '../hooks/usePresets'
import { useConfig } from '../hooks/useConfig'
import { writeText } from '@tauri-apps/plugin-clipboard-manager'
import { useTranslation } from 'react-i18next'

interface PresetsPageProps {
  initialText?: string
  transcriptionId?: string
}

export default function PresetsPage({ initialText = '', transcriptionId }: PresetsPageProps) {
  const { config } = useConfig()
  const { presets, loading, error, loadPresets, applyPreset, applyCustomPrompt } = usePresets(config.apiKey)
  const [inputText, setInputText] = useState(initialText)
  const [customPrompt, setCustomPrompt] = useState('')
  const [result, setResult] = useState('')
  const [applying, setApplying] = useState(false)
  const [copied, setCopied] = useState(false)
  const { t } = useTranslation()

  async function handleApplyPreset(preset: Preset) {
    if (!inputText) return
    setApplying(true)
    try {
      const transformed = await applyPreset(preset, inputText, config.transformModel, transcriptionId)
      setResult(transformed)
    } catch (e) {
      setResult(`Error: ${e}`)
    } finally {
      setApplying(false)
    }
  }

  async function handleCustomTransform() {
    if (!inputText || !customPrompt) return
    setApplying(true)
    try {
      const transformed = await applyCustomPrompt(customPrompt, inputText, config.transformModel, transcriptionId)
      setResult(transformed)
    } catch (e) {
      setResult(`Error: ${e}`)
    } finally {
      setApplying(false)
    }
  }

  async function handleCopy() {
    if (!result) return
    await writeText(result)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="flex flex-col h-full bg-gray-900 text-white p-4 space-y-4 overflow-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">{t('presets.title')}</h2>
        <button
          onClick={loadPresets}
          disabled={loading}
          className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
        >
          {loading ? t('presets.loading') : t('presets.reload')}
        </button>
      </div>

      {/* API key missing warning */}
      {!config.apiKey && (
        <div className="p-3 rounded bg-yellow-900/50 border border-yellow-700 text-yellow-300 text-sm">
          {t('presets.noPresets')}
        </div>
      )}

      {/* Load error */}
      {error && (
        <div className="p-3 rounded bg-red-900/50 border border-red-700 text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="flex gap-4 flex-col lg:flex-row flex-1 min-h-0">
        {/* Left column: presets list */}
        <div className="lg:w-64 flex flex-col space-y-2 flex-shrink-0">
          {loading && (
            <div className="text-gray-400 text-sm text-center py-4">{t('presets.loading')}</div>
          )}
          {!loading && presets.length === 0 && config.apiKey && (
            <div className="text-gray-500 text-sm text-center py-4">{t('presets.empty')}</div>
          )}
          {presets.map((preset) => (
            <div
              key={preset.id}
              className="p-3 rounded-lg bg-gray-800 border border-gray-700 space-y-2"
            >
              <div>
                <p className="font-medium text-sm">{preset.name}</p>
                {preset.description && (
                  <p className="text-xs text-gray-400 mt-0.5">{preset.description}</p>
                )}
              </div>
              <button
                onClick={() => handleApplyPreset(preset)}
                disabled={applying || !inputText}
                className="w-full px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded text-xs font-medium transition-colors"
              >
                {applying ? '...' : t('presets.apply')}
              </button>
            </div>
          ))}
        </div>

        {/* Right column: editor */}
        <div className="flex-1 flex flex-col space-y-3 min-w-0">
          {/* Input text */}
          <div className="space-y-1">
            <label className="text-sm text-gray-400">{t('presets.inputPlaceholder')}</label>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={t('presets.inputPlaceholder')}
              rows={5}
              className="w-full p-3 rounded bg-gray-800 border border-gray-700 text-white text-sm resize-none focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Custom prompt */}
          <div className="space-y-1">
            <label className="text-sm text-gray-400">{t('presets.customPrompt')}</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                placeholder={t('presets.customPromptPlaceholder')}
                className="flex-1 p-2 rounded bg-gray-800 border border-gray-700 text-white text-sm focus:outline-none focus:border-blue-500"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleCustomTransform()
                }}
              />
              <button
                onClick={handleCustomTransform}
                disabled={applying || !inputText || !customPrompt}
                className="px-3 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm font-medium transition-colors whitespace-nowrap"
              >
                {applying ? '...' : t('presets.applyCustom')}
              </button>
            </div>
          </div>

          {/* Result */}
          {result && (
            <div className="space-y-1 flex-1">
              <div className="flex items-center justify-between">
                <label className="text-sm text-gray-400">{t('presets.result')}</label>
                <button
                  onClick={handleCopy}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs font-medium transition-colors"
                >
                  {copied ? t('presets.copied') : t('presets.copy')}
                </button>
              </div>
              <div className="p-3 rounded bg-gray-800 border border-gray-700 text-white text-sm whitespace-pre-wrap min-h-[80px]">
                {result}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
