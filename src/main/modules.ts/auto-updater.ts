/* eslint-disable @typescript-eslint/no-explicit-any */
import { autoUpdater } from 'electron-updater'
import { getMainWindow } from './tray'
import { ipcMain, app } from 'electron'

// Disable auto downloading
autoUpdater.autoDownload = false
autoUpdater.autoInstallOnAppQuit = true

// Track update state
// let updateAvailable = false
// let downloadProgress = 0

export async function initAutoUpdater(): Promise<any> {
  console.info('[AUTO-UPDATER] Initializing auto-updater')

  const mainWindow = getMainWindow()

  if (!mainWindow) {
    console.error('[AUTO-UPDATER] No main window found')
    return
  }

  // Set up IPC handlers
  ipcMain.on('check-for-updates', async () => {
    console.info('[AUTO-UPDATER] Check for updates requested by renderer')
    try {
      await autoUpdater.checkForUpdates()
      console.info('[AUTO-UPDATER] Check for updates initiated')
    } catch (error) {
      console.error('[AUTO-UPDATER] Failed to check for updates:', error)
      mainWindow.webContents.send('update-error', 'Failed to check for updates')
    }
  })

  ipcMain.on('download-update', () => {
    console.info('[AUTO-UPDATER] Download update requested')
    autoUpdater.downloadUpdate()
  })

  ipcMain.on('quit-and-install', () => {
    console.info('[AUTO-UPDATER] Quit and install requested')
    autoUpdater.quitAndInstall()
  })

  // Add handler to get app version
  ipcMain.handle('get-app-version', () => {
    return app.getVersion()
  })

  // Set up event handlers
  autoUpdater.on('checking-for-update', () => {
    console.info('[AUTO-UPDATER] Checking for update')
    try {
      mainWindow.webContents.send('checking-for-updates')
      console.info('[AUTO-UPDATER] Sent checking-for-updates event to renderer')
    } catch (error) {
      console.error('[AUTO-UPDATER] Failed to send checking-for-updates event:', error)
    }
  })

  autoUpdater.on('update-available', (info) => {
    console.info('[AUTO-UPDATER] Update available:', info)
    try {
      mainWindow.webContents.send('update-available', info)
      console.info('[AUTO-UPDATER] Sent update-available event to renderer')
    } catch (error) {
      console.error('[AUTO-UPDATER] Failed to send update-available event:', error)
    }
  })

  autoUpdater.on('update-not-available', (info) => {
    console.info('[AUTO-UPDATER] Update not available:', info)
    try {
      mainWindow.webContents.send('update-not-available', info)
      console.info('[AUTO-UPDATER] Sent update-not-available event to renderer')
    } catch (error) {
      console.error('[AUTO-UPDATER] Failed to send update-not-available event:', error)
    }
  })

  autoUpdater.on('download-progress', (progressObj) => {
    console.info(`[AUTO-UPDATER] Download progress: ${progressObj.percent}%`)
    try {
      mainWindow.webContents.send('download-progress', progressObj)
      console.debug('[AUTO-UPDATER] Sent download-progress event to renderer')
    } catch (error) {
      console.error('[AUTO-UPDATER] Failed to send download-progress event:', error)
    }
  })

  autoUpdater.on('update-downloaded', (info) => {
    console.info('[AUTO-UPDATER] Update downloaded:', info)
    try {
      mainWindow.webContents.send('update-downloaded', info)
      console.info('[AUTO-UPDATER] Sent update-downloaded event to renderer')
    } catch (error) {
      console.error('[AUTO-UPDATER] Failed to send update-downloaded event:', error)
    }
  })

  autoUpdater.on('error', (err) => {
    console.error('[AUTO-UPDATER] Error:', err)
    try {
      mainWindow.webContents.send('update-error', err.message)
      console.info('[AUTO-UPDATER] Sent update-error event to renderer')
    } catch (error) {
      console.error('[AUTO-UPDATER] Failed to send update-error event:', error)
    }
  })

  return autoUpdater
}
