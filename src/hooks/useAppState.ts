import { useState, useCallback } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { writeText } from '@tauri-apps/plugin-clipboard-manager'
import { AppStatus } from '../types'
import { useRecorder } from './useRecorder'
import { useConfig } from './useConfig'
import { useEditFlow } from './useEditFlow'

export function useAppState() {
  const [status, setStatus] = useState<AppStatus>('idle')
  const [lastTranscription, setLastTranscription] = useState('')
  const [lastTranscriptionId, setLastTranscriptionId] = useState<string | undefined>(undefined)
  const [error, setError] = useState<string | null>(null)
  const { config } = useConfig()
  const recorder = useRecorder()

  const editFlow = useEditFlow({
    apiKey: config.apiKey,
    editModel: config.editModel,
    editAutoPaste: config.editAutoPaste,
    editAutoEnter: config.editAutoEnter,
  })

  const updateStatus = useCallback(async (s: AppStatus) => {
    setStatus(s)
    await invoke('update_app_status', { status: s }).catch(() => {})
  }, [])

  const startRecording = useCallback(async () => {
    if (status !== 'idle') return
    try {
      await recorder.startRecording()
      await updateStatus('recording')
    } catch (e) {
      setError(String(e))
      await updateStatus('error')
    }
  }, [status, recorder, updateStatus])

  const stopAndTranscribe = useCallback(async () => {
    if (status !== 'recording') return
    try {
      await updateStatus('processing')
      const audioBytes = await recorder.stopRecording()
      const result = await recorder.transcribeAudio(
        audioBytes,
        config.apiKey,
        config.transcriptionModel,
        config.language,
      )
      const text = result.text
      setLastTranscription(text)
      setLastTranscriptionId(result.transcription_id)
      await writeText(text)
      if (config.autoPaste) {
        // Simular Ctrl+V — se implementará en fase posterior con plugin shell
        // Por ahora solo copiar al clipboard es suficiente
      }
      await updateStatus('success')
      setTimeout(() => updateStatus('idle'), 2000)
    } catch (e) {
      setError(String(e))
      await updateStatus('error')
      setTimeout(() => updateStatus('idle'), 3000)
    }
  }, [status, recorder, config, updateStatus])

  // Edit flow: primer press → startEdit, segundo press → completeEdit
  const handleEditHotkey = useCallback(async () => {
    if (status === 'idle') {
      // Start edit flow
      try {
        await updateStatus('editing')
        await editFlow.startEdit()
      } catch (e) {
        setError(String(e))
        await updateStatus('error')
        setTimeout(() => updateStatus('idle'), 3000)
      }
    } else if (status === 'editing') {
      // Complete edit flow
      try {
        await updateStatus('processing')
        const editedText = await editFlow.completeEdit()
        if (editedText) {
          setLastTranscription(editedText)
        }
        await updateStatus('success')
        setTimeout(() => updateStatus('idle'), 2000)
      } catch (e) {
        setError(String(e))
        await updateStatus('error')
        setTimeout(() => updateStatus('idle'), 3000)
      }
    }
  }, [status, editFlow, updateStatus])

  return {
    status,
    lastTranscription,
    lastTranscriptionId,
    error,
    startRecording,
    stopAndTranscribe,
    handleEditHotkey,
    isRecording: status === 'recording',
    isEditing: status === 'editing',
    audioLevel: recorder.audioLevel,
  }
}
