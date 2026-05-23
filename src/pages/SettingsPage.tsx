import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import i18n from '../i18n'
import { useConfig } from '../hooks/useConfig'
import { invoke } from '@tauri-apps/api/core'
import { platform } from '@tauri-apps/plugin-os'
import type { AppConfig } from '../types'

function Toggle({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!value)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        value ? 'bg-blue-600' : 'bg-gray-600'
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
          value ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  )
}

function SectionHeader({ title }: { title: string }) {
  return (
    <div className="pt-4 pb-1 border-b border-gray-700">
      <h2 className="text-xs font-semibold text-blue-400 uppercase tracking-wider">{title}</h2>
    </div>
  )
}

export default function SettingsPage() {
  const { t } = useTranslation()
  const { config, saveConfig } = useConfig()
  const [saved, setSaved] = useState(false)
  const [showApiKey, setShowApiKey] = useState(false)
  const [audioDevices, setAudioDevices] = useState<string[]>([])
  const [isWindows, setIsWindows] = useState(false)

  // Local state for controlled inputs
  const [localApiKey, setLocalApiKey] = useState(config.apiKey)
  const [localHotkey, setLocalHotkey] = useState(config.hotkey)
  const [localEditHotkey, setLocalEditHotkey] = useState(config.editHotkey)
  const [localTransformModel, setLocalTransformModel] = useState(config.transformModel)
  const [localEditModel, setLocalEditModel] = useState(config.editModel)

  // Sync local state when config loads
  useEffect(() => {
    setLocalApiKey(config.apiKey)
    setLocalHotkey(config.hotkey)
    setLocalEditHotkey(config.editHotkey)
    setLocalTransformModel(config.transformModel)
    setLocalEditModel(config.editModel)
  }, [config.apiKey, config.hotkey, config.editHotkey, config.transformModel, config.editModel])

  useEffect(() => {
    invoke<string[]>('list_audio_devices')
      .then(setAudioDevices)
      .catch(() => setAudioDevices([]))

    setIsWindows(platform() === 'windows')
  }, [])

  async function handleSave() {
    const updates = {
      apiKey: localApiKey,
      hotkey: localHotkey,
      editHotkey: localEditHotkey,
      transformModel: localTransformModel,
      editModel: localEditModel,
    }
    await saveConfig(updates)

    // Re-register hotkeys if they changed
    if (localHotkey !== config.hotkey || localEditHotkey !== config.editHotkey) {
      await invoke('register_hotkeys', {
        recordHotkey: localHotkey,
        editHotkey: localEditHotkey,
      }).catch(console.error)
    }

    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const inputClass =
    'w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500'
  const selectClass = inputClass
  const labelClass = 'block text-sm font-medium text-gray-300'
  const rowClass = 'flex items-center justify-between'

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-lg mx-auto space-y-4">
        <h1 className="text-2xl font-bold text-white">{t('settings.title')}</h1>

        {/* ── API & Models ── */}
        <SectionHeader title={t('settings.sections.api')} />

        <div className="space-y-1">
          <label className={labelClass}>{t('settings.apiKey')}</label>
          <div className="relative">
            <input
              type={showApiKey ? 'text' : 'password'}
              value={localApiKey}
              onChange={(e) => setLocalApiKey(e.target.value)}
              placeholder={t('settings.apiKeyPlaceholder')}
              className={inputClass + ' pr-16'}
            />
            <button
              type="button"
              onClick={() => setShowApiKey((v) => !v)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-400 hover:text-gray-200 px-1"
            >
              {showApiKey ? 'Hide' : 'Show'}
            </button>
          </div>
        </div>

        <div className="space-y-1">
          <label className={labelClass}>{t('settings.transcriptionModel')}</label>
          <select
            value={config.transcriptionModel}
            onChange={(e) => saveConfig({ transcriptionModel: e.target.value as 'v3-turbo' | 'v3' })}
            className={selectClass}
          >
            <option value="v3-turbo">v3-turbo</option>
            <option value="v3">v3</option>
          </select>
        </div>

        <div className="space-y-1">
          <label className={labelClass}>{t('settings.transcriptionLanguage')}</label>
          <select
            value={config.language}
            onChange={(e) => saveConfig({ language: e.target.value as 'es' | 'en' | 'de' })}
            className={selectClass}
          >
            <option value="auto">{t('languages.auto')}</option>
            <option value="es">{t('languages.es')}</option>
            <option value="en">{t('languages.en')}</option>
            <option value="de">{t('languages.de')}</option>
          </select>
        </div>

        <div className="space-y-1">
          <label className={labelClass}>{t('settings.transformModel')}</label>
          <input
            type="text"
            value={localTransformModel}
            onChange={(e) => setLocalTransformModel(e.target.value)}
            className={inputClass}
          />
        </div>

        <div className="space-y-1">
          <label className={labelClass}>{t('settings.editModel')}</label>
          <input
            type="text"
            value={localEditModel}
            onChange={(e) => setLocalEditModel(e.target.value)}
            className={inputClass}
          />
        </div>

        {/* ── Hotkeys ── */}
        <SectionHeader title={t('settings.sections.hotkeys')} />

        <div className="space-y-1">
          <label className={labelClass}>{t('settings.recordHotkey')}</label>
          <input
            type="text"
            value={localHotkey}
            onChange={(e) => setLocalHotkey(e.target.value)}
            className={inputClass}
          />
        </div>

        <div className="space-y-1">
          <label className={labelClass}>{t('settings.editHotkeyLabel')}</label>
          <input
            type="text"
            value={localEditHotkey}
            onChange={(e) => setLocalEditHotkey(e.target.value)}
            className={inputClass}
          />
        </div>

        {/* ── Behavior ── */}
        <SectionHeader title={t('settings.sections.behavior')} />

        <div className={rowClass}>
          <label className={labelClass}>{t('settings.autoPaste')}</label>
          <Toggle value={config.autoPaste} onChange={(v) => saveConfig({ autoPaste: v })} />
        </div>

        <div className={rowClass}>
          <label className={labelClass}>{t('settings.autoEnter')}</label>
          <Toggle value={config.autoEnter} onChange={(v) => saveConfig({ autoEnter: v })} />
        </div>

        <div className={rowClass}>
          <label className={labelClass}>{t('settings.editAutoPaste')}</label>
          <Toggle value={config.editAutoPaste} onChange={(v) => saveConfig({ editAutoPaste: v })} />
        </div>

        <div className={rowClass}>
          <label className={labelClass}>{t('settings.editAutoEnter')}</label>
          <Toggle value={config.editAutoEnter} onChange={(v) => saveConfig({ editAutoEnter: v })} />
        </div>

        {/* ── Audio ── */}
        <SectionHeader title={t('settings.sections.audio')} />

        <div className="space-y-1">
          <label className={labelClass}>{t('settings.microphone')}</label>
          <select
            value={config.microphoneDevice}
            onChange={(e) => saveConfig({ microphoneDevice: e.target.value })}
            className={selectClass}
          >
            <option value="">Default</option>
            {audioDevices.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        {isWindows && (
          <div className={rowClass}>
            <label className={labelClass}>{t('settings.systemAudio')}</label>
            <Toggle value={config.systemAudio} onChange={(v) => saveConfig({ systemAudio: v })} />
          </div>
        )}

        {/* ── Overlay ── */}
        <SectionHeader title={t('settings.sections.overlay')} />

        <div className={rowClass}>
          <label className={labelClass}>{t('settings.persistentOverlay')}</label>
          <Toggle value={config.overlayPersistent} onChange={(v) => saveConfig({ overlayPersistent: v })} />
        </div>

        <div className="space-y-1">
          <label className={labelClass}>
            {t('settings.overlayOpacity')}: {Math.round(config.overlayOpacity * 100)}%
          </label>
          <input
            type="range"
            min={0.5}
            max={1.0}
            step={0.05}
            value={config.overlayOpacity}
            onChange={(e) => saveConfig({ overlayOpacity: parseFloat(e.target.value) })}
            className="w-full accent-blue-500"
          />
        </div>

        <div className="space-y-1">
          <label className={labelClass}>{t('settings.overlayPosition')}</label>
          <select
            value={config.overlayPosition}
            onChange={(e) =>
              saveConfig({ overlayPosition: e.target.value as AppConfig['overlayPosition'] })
            }
            className={selectClass}
          >
            <option value="top-left">Top Left</option>
            <option value="top-right">Top Right</option>
            <option value="bottom-left">Bottom Left</option>
            <option value="bottom-right">Bottom Right</option>
          </select>
        </div>

        {/* ── Interface ── */}
        <SectionHeader title={t('settings.sections.interface')} />

        <div className="space-y-1">
          <label className={labelClass}>{t('settings.uiLanguage')}</label>
          <select
            value={config.uiLanguage}
            onChange={(e) => {
              const lang = e.target.value as 'es' | 'en' | 'de'
              saveConfig({ uiLanguage: lang })
              i18n.changeLanguage(lang)
            }}
            className={selectClass}
          >
            <option value="es">{t('languages.es')}</option>
            <option value="en">{t('languages.en')}</option>
            <option value="de">{t('languages.de')}</option>
          </select>
        </div>

        <div className={rowClass}>
          <label className={labelClass}>{t('settings.alwaysOnTop')}</label>
          <Toggle
            value={config.alwaysOnTop}
            onChange={(v) => {
              saveConfig({ alwaysOnTop: v })
              invoke('set_always_on_top', { value: v }).catch(console.error)
            }}
          />
        </div>

        {/* Save Button */}
        <div className="pt-4">
          <button
            onClick={handleSave}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg transition-colors"
          >
            {saved ? t('settings.saved') : t('settings.save')}
          </button>
        </div>
      </div>
    </div>
  )
}

