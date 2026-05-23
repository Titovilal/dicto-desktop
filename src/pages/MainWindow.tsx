import { useCallback, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAppState } from '../hooks/useAppState'
import { useHotkeys } from '../hooks/useHotkeys'
import Waveform from '../components/ui/Waveform'
import { invoke } from '@tauri-apps/api/core'
import PresetsPage from './PresetsPage'
import SettingsPage from './SettingsPage'

type Tab = 'transcription' | 'presets' | 'settings'

const STATUS_COLORS: Record<string, string> = {
  idle: 'text-gray-400',
  recording: 'text-red-400',
  processing: 'text-orange-400',
  success: 'text-green-400',
  error: 'text-red-600',
  editing: 'text-blue-400',
}

const STATUS_DOT_COLORS: Record<string, string> = {
  idle: 'bg-gray-500',
  recording: 'bg-red-500 animate-pulse',
  processing: 'bg-orange-500 animate-pulse',
  success: 'bg-green-500',
  error: 'bg-red-700',
  editing: 'bg-blue-500',
}

export default function MainWindow() {
  const { t } = useTranslation()
  const [overlayVisible, setOverlayVisible] = useState(false)
  const [activeTab, setActiveTab] = useState<Tab>('transcription')
  const {
    status,
    lastTranscription,
    lastTranscriptionId,
    error,
    startRecording,
    stopAndTranscribe,
    handleEditHotkey,
    isRecording,
    isEditing,
    audioLevel,
  } = useAppState()

  const handleRecordHotkey = useCallback(() => {
    if (isRecording) {
      stopAndTranscribe()
    } else {
      startRecording()
    }
  }, [isRecording, startRecording, stopAndTranscribe])

  useHotkeys(handleRecordHotkey, handleEditHotkey)

  const isProcessing = status === 'processing'

  const tabs: { key: Tab; label: string }[] = [
    { key: 'transcription', label: t('tabs.transcription') },
    { key: 'presets', label: t('tabs.presets') },
    { key: 'settings', label: t('tabs.settings') },
  ]

  return (
    <div className="flex flex-col min-h-screen bg-gray-900 text-white">
      {/* Tab bar */}
      <div className="flex border-b border-gray-700 bg-gray-800">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-5 py-3 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? 'text-white border-b-2 border-blue-500'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'transcription' && (
          <div className="flex flex-col items-center justify-center min-h-full p-8">
            <div className="w-full max-w-md space-y-6">
              <div className="text-center">
                <h1 className="text-3xl font-bold">{t('app.name')}</h1>
                <div className="flex items-center justify-center gap-2 mt-2">
                  <span className={`w-2 h-2 rounded-full ${STATUS_DOT_COLORS[status] ?? 'bg-gray-500'}`} />
                  <p className={`text-sm font-medium ${STATUS_COLORS[status] ?? 'text-gray-400'}`}>
                    {t(`app.status.${status}`, { defaultValue: status })}
                  </p>
                </div>
              </div>

              {/* Waveform */}
              <div className="flex items-center justify-center h-16">
                {isRecording ? (
                  <Waveform level={audioLevel} bars={14} color="#f87171" />
                ) : isEditing ? (
                  <Waveform level={audioLevel} bars={14} color="#60a5fa" />
                ) : isProcessing ? (
                  <Waveform level={0.5} bars={14} color="#fb923c" />
                ) : (
                  <div className="text-gray-600 text-sm">
                    {t('app.pressRecord', { defaultValue: 'Pulsa Grabar o usa el hotkey global' })}
                  </div>
                )}
              </div>

              {/* Overlay toggle */}
              <div className="flex justify-center">
                <button
                  onClick={async () => {
                    if (overlayVisible) {
                      await invoke('hide_overlay')
                      setOverlayVisible(false)
                    } else {
                      await invoke('show_overlay')
                      setOverlayVisible(true)
                    }
                  }}
                  className="px-4 py-1.5 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
                >
                  {overlayVisible
                    ? t('app.hideOverlay', { defaultValue: 'Ocultar Overlay' })
                    : t('app.showOverlay', { defaultValue: 'Mostrar Overlay' })}
                </button>
              </div>

              {/* Buttons */}
              <div className="flex gap-3 justify-center">
                {!isRecording ? (
                  <button
                    onClick={startRecording}
                    disabled={isProcessing}
                    className="px-6 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-medium transition-colors"
                  >
                    {t('app.record', { defaultValue: 'Grabar' })}
                  </button>
                ) : (
                  <button
                    onClick={stopAndTranscribe}
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
                  >
                    {t('app.stopTranscribe', { defaultValue: 'Parar y Transcribir' })}
                  </button>
                )}
              </div>

              {/* Error */}
              {error && (
                <div className="p-3 rounded bg-red-900/50 border border-red-700 text-red-300 text-sm">
                  {error}
                </div>
              )}

              {/* Transcription result */}
              {lastTranscription && (
                <div className="space-y-1">
                  <label className="text-sm text-gray-400">
                    {t('app.transcription', { defaultValue: 'Transcripción' })}
                  </label>
                  <div className="p-3 rounded bg-gray-800 border border-gray-700 text-white text-sm whitespace-pre-wrap">
                    {lastTranscription}
                  </div>
                  {lastTranscription && (
                    <button
                      onClick={() => setActiveTab('presets')}
                      className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      {t('tabs.presets')} →
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'presets' && (
          <PresetsPage
            initialText={lastTranscription}
            transcriptionId={lastTranscriptionId}
          />
        )}

        {activeTab === 'settings' && <SettingsPage />}
      </div>
    </div>
  )
}
