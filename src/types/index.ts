export type AppStatus = 'idle' | 'recording' | 'processing' | 'editing' | 'success' | 'error'

export type TranscriptionModel = 'v3-turbo' | 'v3'

export interface AppConfig {
  apiKey: string
  language: 'es' | 'en' | 'de'
  uiLanguage: 'es' | 'en' | 'de'
  transcriptionModel: TranscriptionModel
  transformModel: string
  editModel: string
  hotkey: string
  editHotkey: string
  autoPaste: boolean
  autoEnter: boolean
  editAutoPaste: boolean
  editAutoEnter: boolean
  overlayPosition: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'center'
  overlayPersistent: boolean
  overlayOpacity: number
  alwaysOnTop: boolean
  systemAudio: boolean
  microphoneDevice: string
}

export const DEFAULT_CONFIG: AppConfig = {
  apiKey: '',
  language: 'es',
  uiLanguage: 'es',
  transcriptionModel: 'v3-turbo',
  transformModel: 'qwen/qwen3-32b',
  editModel: 'qwen/qwen3-32b',
  hotkey: 'CommandOrControl+Shift+Space',
  editHotkey: 'CommandOrControl+Alt+Space',
  autoPaste: true,
  autoEnter: false,
  editAutoPaste: true,
  editAutoEnter: false,
  overlayPosition: 'bottom-right',
  overlayPersistent: false,
  overlayOpacity: 0.95,
  alwaysOnTop: false,
  systemAudio: false,
  microphoneDevice: '',
}
