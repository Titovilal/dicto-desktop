/* eslint-disable @typescript-eslint/no-explicit-any */
import { autoUpdater } from 'electron-updater'
import { getMainWindow } from './tray'
import { app, ipcMain } from 'electron'

// Enable auto downloading
autoUpdater.autoDownload = true
autoUpdater.autoInstallOnAppQuit = true

// Track update state
let updateDownloaded = false

// Helper function to send messages to the renderer
function sendStatusToWindow(message: string, data?: any): void {
  console.info(`[AUTO-UPDATER] ${message}`, data || '')
  const mainWindow = getMainWindow()
  if (mainWindow) {
    try {
      if (data) {
        mainWindow.webContents.send(message, data)
      } else {
        mainWindow.webContents.send(message)
      }
    } catch (error) {
      console.error(`[AUTO-UPDATER] Failed to send ${message} to window:`, error)
    }
  } else {
    console.error(`[AUTO-UPDATER] No main window found when sending: ${message}`)
  }
}

export async function initAutoUpdater(): Promise<any> {
  console.info('[AUTO-UPDATER] Initializing auto-updater')

  // Set up IPC handlers
  ipcMain.on('check-for-updates', async () => {
    console.info('[AUTO-UPDATER] Check for updates requested by renderer')
    try {
      await autoUpdater.checkForUpdates()
    } catch (error) {
      console.error('[AUTO-UPDATER] Failed to check for updates:', error)
    }
  })

  ipcMain.on('restart-and-install', () => {
    console.info('[AUTO-UPDATER] Restart and install requested')
    try {
      autoUpdater.quitAndInstall(false, true)
    } catch (error) {
      console.error('[AUTO-UPDATER] Failed to restart and install:', error)
    }
  })

  // Add handler to get app version
  ipcMain.handle('get-app-version', () => {
    return app.getVersion()
  })

  // Add handler to check if update is already downloaded
  ipcMain.handle('is-update-downloaded', () => {
    return updateDownloaded
  })

  // Set up event handlers
  autoUpdater.on('update-downloaded', (info) => {
    console.info('[AUTO-UPDATER] Update downloaded:', info)
    updateDownloaded = true
    sendStatusToWindow('update-downloaded', info)
  })

  autoUpdater.on('error', (err) => {
    console.error('[AUTO-UPDATER] Error:', err)
  })

  // Check for updates on startup
  setTimeout(() => {
    console.info('[AUTO-UPDATER] Checking for updates on startup')
    autoUpdater.checkForUpdates().catch((err) => {
      console.error('[AUTO-UPDATER] Initial check failed:', err)
    })
  }, 3000)

  return autoUpdater
}
