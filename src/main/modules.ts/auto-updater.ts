/* eslint-disable @typescript-eslint/no-explicit-any */
import { app, ipcMain } from 'electron'
import { autoUpdater, UpdateCheckResult } from 'electron-updater'
import { getMainWindow } from './tray'
// Disable auto downloading
autoUpdater.autoDownload = false

// Track update state
let updateAvailable = false
let downloadProgress = 0

export async function initAutoUpdater(): Promise<any> {
  console.log('[AUTO-UPDATER] Initializing auto-updater')

  const mainWindow = getMainWindow()

  if (!mainWindow) {
    console.error('[AUTO-UPDATER] No main window found')
    return
  }

  // Register IPC handlers
  ipcMain.handle('check-for-updates', async (): Promise<UpdateCheckResult | null> => {
    console.log('[AUTO-UPDATER] Checking for updates...')
    try {
      return await autoUpdater.checkForUpdates()
    } catch (error) {
      console.log('[AUTO-UPDATER] Error checking for updates:', error)
      throw error
    }
  })

  ipcMain.handle('download-update', async () => {
    console.log('[AUTO-UPDATER] Starting download...')
    try {
      await autoUpdater.downloadUpdate()
      return true
    } catch (error) {
      console.log('[AUTO-UPDATER] Error downloading update:', error)
      throw error
    }
  })

  ipcMain.handle('install-update', () => {
    console.log('[AUTO-UPDATER] Installing update...')
    autoUpdater.quitAndInstall(false, true)
  })

  ipcMain.handle('get-update-status', () => {
    return {
      updateAvailable,
      downloadProgress
    }
  })

  // Handle updater events
  autoUpdater.on('checking-for-update', () => {
    console.log('[AUTO-UPDATER] Checking for update...')
    mainWindow.webContents.send('update-status', { status: 'checking' })
  })

  autoUpdater.on('update-available', (info) => {
    console.log('[AUTO-UPDATER] Update available:', info)
    updateAvailable = true
    mainWindow.webContents.send('update-status', {
      status: 'available',
      info: {
        version: info.version,
        releaseDate: info.releaseDate
      }
    })
  })

  autoUpdater.on('update-not-available', (info) => {
    console.log('[AUTO-UPDATER] Update not available:', info)
    updateAvailable = false
    mainWindow.webContents.send('update-status', {
      status: 'not-available',
      info: {
        version: info.version,
        releaseDate: info.releaseDate
      }
    })
  })

  autoUpdater.on('download-progress', (progressObj) => {
    downloadProgress = progressObj.percent
    console.log(`[AUTO-UPDATER] Download progress: ${downloadProgress}%`)
    mainWindow.webContents.send('update-status', {
      status: 'downloading',
      progress: progressObj
    })
  })

  autoUpdater.on('update-downloaded', (info) => {
    console.log('[AUTO-UPDATER] Update downloaded:', info)
    mainWindow.webContents.send('update-status', {
      status: 'downloaded',
      info: {
        version: info.version,
        releaseDate: info.releaseDate
      }
    })
  })

  autoUpdater.on('error', (err) => {
    console.log('[AUTO-UPDATER] Error:', err)
    mainWindow.webContents.send('update-status', {
      status: 'error',
      error: err.message
    })
  })

  // Check for updates automatically after startup (with a delay to not slow down app startup)
  setTimeout(() => {
    if (process.env.NODE_ENV !== 'development') {
      autoUpdater.checkForUpdates().catch((err) => {
        console.log('[AUTO-UPDATER] Error checking for updates on startup:', err)
      })
    }
  }, 10000)

  // Re-check for updates periodically (every 4 hours)
  setInterval(
    () => {
      if (process.env.NODE_ENV !== 'development') {
        autoUpdater.checkForUpdates().catch((err) => {
          console.log('[AUTO-UPDATER] Error checking for updates in interval:', err)
        })
      }
    },
    4 * 60 * 60 * 1000
  )

  // Clean up IPC handlers when app is quitting
  app.on('will-quit', () => {
    ipcMain.removeHandler('check-for-updates')
    ipcMain.removeHandler('download-update')
    ipcMain.removeHandler('install-update')
    ipcMain.removeHandler('get-update-status')
  })

  return autoUpdater
}
