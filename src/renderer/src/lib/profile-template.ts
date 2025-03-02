import { Profile } from '@/types/types'

export const getNewProfileTemplate = (name: string): Profile => ({
    name,
    prompt: '',
    useAI: false,
    copyToClipboard: true,
    language: 'english',
    returnBoth: false,
    autoPaste: false,
    autoEnter: false,
    useSelectedText: false,
    modelName: 'gemini-flash-2.0',
    temperature: 0.7,
    transcriptionPrompt: 'Transcribe the following audio:'
})