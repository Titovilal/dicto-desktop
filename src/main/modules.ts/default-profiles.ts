import { Profile } from '../../renderer/src/types/types'

export const DEFAULT_PROFILES: Profile[] = [
  {
    name: 'Default',
    prompt: '',
    useAI: false,
    copyToClipboard: true,
    language: 'english',
    returnBoth: false,
    autoPaste: false,
    autoEnter: false,
    useSelectedText: false,
    modelName: 'google/gemini-2.0-flash-001',
    temperature: 0.3,
    transcriptionPrompt: 'Transcribe the following audio:',
    onlyLlm: false
  },
  {
    name: 'AI Assistant',
    prompt: 'Act as a helpful assistant and improve the following transcription:',
    useAI: true,
    copyToClipboard: true,
    language: 'english',
    returnBoth: true,
    autoPaste: false,
    autoEnter: false,
    useSelectedText: false,
    modelName: 'google/gemini-2.0-flash-001',
    temperature: 0.7,
    transcriptionPrompt: 'Transcribe the following audio:',
    onlyLlm: false
  },
  {
    name: 'Quick Copy',
    prompt: '',
    useAI: false,
    copyToClipboard: true,
    language: 'english',
    returnBoth: false,
    autoPaste: true,
    autoEnter: true,
    useSelectedText: false,
    modelName: 'google/gemini-2.0-flash-001',
    temperature: 0.3,
    transcriptionPrompt: 'Transcribe the following audio:',
    onlyLlm: false
  }
]
