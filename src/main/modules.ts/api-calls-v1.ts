import { App, globalShortcut, ipcMain, BrowserWindow, protocol } from "electron";
import path from 'path';
import { Profile } from '../../renderer/src/types/types';
import { getClipboardText, setClipboardText, simulateCopy, simulateEnter, simulatePaste } from "./clipboard-and-keys";
import { showRecordingPopup, updatePopupState, hideRecordingPopup, PopupState } from './popup-window';

let currentRegisteredShortcut: string;

const dictoWebUrl = 'https://www.dicto.io/api/v1'
// const dictoWebUrl = 'http://localhost:3000/api/v1'


function registerGlobalShortcut(shortcut: string) {
  if (currentRegisteredShortcut) {
    globalShortcut.unregister(currentRegisteredShortcut);
  }

  try {
    const success = globalShortcut.register(shortcut, () => {
      console.log('[API CALLS V1] Shortcut triggered');
      // Get the main window specifically
      const mainWindow = BrowserWindow.getAllWindows().find(window =>
        !window.webContents.getURL().includes('index-popup.html')
      );

      if (mainWindow) {
        mainWindow.webContents.send('toggle-recording');
      } else {
        console.error('[API CALLS V1] Main window not found');
      }
    });

    if (success) {
      currentRegisteredShortcut = shortcut;
      console.log(`[API CALLS V1] Shortcut ${shortcut} registered successfully`);
    } else {
      console.error(`[API CALLS V1] Failed to register shortcut ${shortcut}`);
    }
  } catch (error) {
    console.error(`[API CALLS V1] Error registering shortcut ${shortcut}:`, error);
  }
}

interface ProcessRecordingParams {
  audioData: Uint8Array;
  profile: Profile;
  apiKey: string;
}

async function processRecording({ audioData, profile, apiKey }: ProcessRecordingParams) {
  try {
    if (!profile) {
      throw new Error('[API_CALLS_V1] No profile selected')
    }

    if (!apiKey) {
      throw new Error('[API_CALLS_V1] No API key provided')
    }

    // Show the recording popup with processing state
    showRecordingPopup('processing');

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

    if (profile.useSelectedText && profile.useAI) {
      await simulateCopy()
      const selectedText = getClipboardText()
      if (selectedText?.trim()) {
        formData.append('selectedText', selectedText)
      }
    }

    // console.log("[API CALLS V1] Data sent to Dicto API:", formData)

    const response = await fetch(`${dictoWebUrl}/get-transcription`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`
      },
      body: formData
    })

    if (response.status !== 200) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json();

    // Copy to clipboard
    if (profile.copyToClipboard) {
      const textToCopy = profile.useAI ? result.data.processed ?? '' : result.data.text ?? ''
      setClipboardText(textToCopy)
    }

    // Auto paste
    if (profile.autoPaste) {
      await simulatePaste()
    }

    // Auto enter
    if (profile.autoEnter) {
      await simulateEnter()
    }

    // When processing is complete, update the popup state to finished
    updatePopupState('finished');

    // Hide the popup after a short delay
    setTimeout(() => {
      hideRecordingPopup();
    }, 2000);

    return {
      transcription: result.data.text ?? '',
      processedText: result.data.processed ?? ''
    }
  } catch (error) {
    console.error('[API CALLS V1] Error processing recording:', error)
    // Hide popup on error
    hideRecordingPopup();
    throw error
  }
}

async function getUserData(apiKey: string) {
  try {
    const response = await fetch(`${dictoWebUrl}/get-user-data`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`[API CALLS V1] HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log("result", result)
    return result.data;
  } catch (error) {
    console.error('[API CALLS V1] Error fetching user data:', error);
    throw error;
  }
}

export async function initApiCallsV1(initialShortcut: string, app: App) {
  // Configuramos el protocolo para manejar los recursos estáticos
  protocol.registerFileProtocol('app', (request, callback) => {
    const url = request.url.substr(6)
    callback({ path: path.normalize(`${__dirname}/${url}`) })
  })

  registerGlobalShortcut(initialShortcut);

  app.on('will-quit', () => {
    globalShortcut.unregisterAll();
    ipcMain.removeHandler('update-shortcut');
    ipcMain.removeHandler('process-recording');
    ipcMain.removeHandler('get-user-data');
    ipcMain.removeHandler('show-popup');
    ipcMain.removeHandler('update-popup-state');
    ipcMain.removeHandler('hide-popup');
  });


  ipcMain.handle('update-shortcut', async (_, newShortcut: string) => {
    registerGlobalShortcut(newShortcut);
    return true;
  });

  ipcMain.handle('process-recording', async (_, params: ProcessRecordingParams) => {
    return await processRecording(params);
  });

  ipcMain.handle('get-user-data', async (_, apiKey: string) => {
    return await getUserData(apiKey);
  });

  ipcMain.handle('show-popup', async (_, state: PopupState) => {
    showRecordingPopup(state);
  });

  ipcMain.handle('update-popup-state', async (_, state: PopupState) => {
    console.log('[API CALLS V1] Updating popup state to:', state);
    updatePopupState(state);
    return true;
  });

  ipcMain.handle('hide-popup', async () => {
    console.log('[API CALLS V1] Hiding popup');
    hideRecordingPopup();
    return true;
  });
}
