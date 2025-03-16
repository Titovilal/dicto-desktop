import { AI_MODELS, ONLY_LLM_MODELS } from '../lib/models'

export interface Profile {
  name: string
  prompt: string
  useAI: boolean
  copyToClipboard: boolean
  language: string
  returnBoth: boolean
  autoPaste: boolean
  autoEnter: boolean
  useSelectedText: boolean
  modelName: keyof typeof AI_MODELS | keyof typeof ONLY_LLM_MODELS
  temperature: number
  transcriptionPrompt: string
  onlyLlm: boolean
}

export interface User {
  email: string
  name: string
  sub_credits: number
  otp_credits: number
  has_access: boolean
  sub_date_time: string | null
  otp_date_time: string | null
  has_subscription: boolean
  cancel_next_month: boolean
  created_at: string
  updated_at: string
}

export interface StoreSchema {
  settings?: {
    theme: 'light' | 'dark'
    appLanguage: string
    soundEnabled: boolean
    soundVolume: number
    recordShortcut: string
    selectedProfile: string
    apiKey: string
    changeProfileShortcut: string
  }
  profiles?: Profile[]
  user?: User
}
