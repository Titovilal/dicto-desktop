import { App, ipcMain, protocol } from 'electron'
import path from 'path'
import { Profile } from '../../renderer/src/types/types'
import {
  getClipboardText,
  setClipboardText,
  simulateCopy,
  simulateEnter,
  simulatePaste
} from './clipboard-and-keys'
import {
  initPopupWindow,
  showRecordingPopup,
  updatePopupState,
  hideRecordingPopup
} from './popup-window'

let popupApi: ReturnType<typeof initPopupWindow>

const endpointUrl = 'https://www.dicto.io/api/v1'
// const endpointUrl = 'http://localhost:3000/api/v1'

interface ProcessRecordingParams {
  audioData: Uint8Array
  profile: Profile
  apiKey: string
}

async function processRecording({
  audioData,
  profile,
  apiKey
}: ProcessRecordingParams): Promise<{ transcription: string; processedText: string }> {
  try {
    if (!profile) {
      throw new Error('[API_CALLS_V1] No profile selected')
    }

    if (!apiKey) {
      throw new Error('[API_CALLS_V1] No API key provided')
    }

    // Show the recording popup with processing state
    showRecordingPopup('processing')

    const formData = new FormData()
    const audioBlob = new Blob([audioData], { type: 'audio/webm' })

    // Añadir los parámetros según el perfil seleccionado
    formData.append('file', audioBlob, 'recording.webm')
    formData.append('language', profile.language)
    formData.append('useAI', profile.useAI.toString())
    formData.append('returnBoth', profile.returnBoth.toString())
    formData.append('modelName', profile.modelName)
    formData.append('temperature', profile.temperature.toString())

    // Solo añadir los prompts si tienen contenido
    if (profile.transcriptionPrompt?.trim()) {
      formData.append('transcriptionPrompt', profile.transcriptionPrompt.trim())
    }
    if (profile.prompt?.trim() && profile.useAI) {
      formData.append('prompt', profile.prompt.trim())
    }
    let selectedText
    if ((profile.useSelectedText && profile.useAI) || profile.onlyLlm) {
      await simulateCopy()
      selectedText = getClipboardText()
      if (selectedText?.trim()) {
        formData.append('selectedText', selectedText)
      }
    }

    // TODO: Fix the way we do this
    let fetchResponse
    if (profile.onlyLlm) {
      const formtDataAi = new FormData()
      formtDataAi.append('file', audioBlob, 'recording.webm')
      formtDataAi.append('modelName', 'gemini-2.0-pro-exp-02-05') // gemini-2.0-flash
      formtDataAi.append('selectedText', selectedText)

      fetchResponse = await fetch(`${endpointUrl}/transcriptions-ai`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${apiKey}`
        },
        body: formtDataAi
      })
    } else {
      fetchResponse = await fetch(`${endpointUrl}/transcriptions`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${apiKey}`
        },
        body: formData
      })
    }

    const result = await fetchResponse.json()

    // Copy to clipboard
    if (profile.copyToClipboard || profile.onlyLlm) {
      const textToCopy =
        profile.useAI || profile.onlyLlm ? (result.data.processed ?? '') : (result.data.text ?? '')
      setClipboardText(textToCopy)
    }
    // Auto paste
    if (profile.autoPaste || profile.onlyLlm) {
      await simulatePaste()
    }
    // Auto enter
    if (profile.autoEnter) {
      await simulateEnter()
    }

    // When processing is complete, update the popup state to finished
    updatePopupState('finished')

    // Hide the popup after a short delay
    setTimeout(() => {
      hideRecordingPopup()
    }, 2000)

    return {
      transcription: result.data.text ?? '',
      processedText: result.data.processed ?? ''
    }
  } catch (error) {
    console.error('[API CALLS V1] Error processing recording:', error)
    // Hide popup on error
    hideRecordingPopup()
    throw error
  }
}

async function getUserData(apiKey: string): Promise<{
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
}> {
  try {
    const response = await fetch(`${endpointUrl}/users`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error(`[API CALLS V1] HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    console.log('result', result)
    return result.data
  } catch (error) {
    console.error('[API CALLS V1] Error fetching user data:', error)
    throw error
  }
}

export async function initApiCallsV1(app: App): Promise<void> {
  // Initialize popup API only once
  if (!popupApi) {
    popupApi = initPopupWindow()
  }

  // Configure protocol for static resources
  protocol.registerFileProtocol('app', (request, callback) => {
    const url = request.url.substr(6)
    callback({ path: path.normalize(`${__dirname}/${url}`) })
  })

  // Register API-related IPC handlers
  ipcMain.handle('process-recording', async (_, params: ProcessRecordingParams) => {
    return await processRecording(params)
  })

  ipcMain.handle('get-user-data', async (_, apiKey: string) => {
    return await getUserData(apiKey)
  })

  // Clean up handlers when app is quitting
  app.on('will-quit', () => {
    ipcMain.removeHandler('process-recording')
    ipcMain.removeHandler('get-user-data')
  })
}
