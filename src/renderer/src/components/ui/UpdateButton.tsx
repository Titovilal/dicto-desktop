/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect } from 'react'
import { HardDriveDownload, RefreshCw, Check, X, Download } from 'lucide-react'

export function UpdateButton(): JSX.Element | null {
  const [updateStatus, setUpdateStatus] = useState<
    'checking' | 'available' | 'not-available' | 'downloading' | 'downloaded' | 'error'
  >('not-available')
  const [updateProgress, setUpdateProgress] = useState(0)
  const [updateError, setUpdateError] = useState('')

  useEffect(() => {
    // Listen for update events from main process
    window.electron.ipcRenderer.on('checking-for-updates', () => {
      window.logger.info('[UpdateButton] Received checking-for-updates event')
      setUpdateStatus('checking')
    })

    window.electron.ipcRenderer.on('update-available', (info: any) => {
      window.logger.info(`[UpdateButton] Received update-available event: ${JSON.stringify(info)}`)
      setUpdateStatus('available')
    })

    window.electron.ipcRenderer.on('update-not-available', () => {
      window.logger.info('[UpdateButton] Received update-not-available event')
      setUpdateStatus('not-available')
    })

    window.electron.ipcRenderer.on('download-progress', (progress: { percent: number }) => {
      window.logger.info(`[UpdateButton] Received download-progress event: ${progress.percent}%`)
      setUpdateStatus('downloading')
      setUpdateProgress(progress.percent)
    })

    window.electron.ipcRenderer.on('update-downloaded', () => {
      window.logger.info('[UpdateButton] Received update-downloaded event')
      setUpdateStatus('downloaded')
    })

    window.electron.ipcRenderer.on('update-error', (error: string) => {
      window.logger.error(`[UpdateButton] Received update-error event: ${error}`)
      setUpdateStatus('error')
      setUpdateError(error)
    })

    // Log initial state
    window.logger.info(`[UpdateButton] Initial update status: ${updateStatus}`)

    // Request check for updates after setting up listeners
    window.logger.info('[UpdateButton] Requesting check for updates')
    window.electron.ipcRenderer.send('check-for-updates')

    return (): void => {
      // Cleanup listeners
      window.electron.ipcRenderer.removeAllListeners('checking-for-updates')
      window.electron.ipcRenderer.removeAllListeners('update-available')
      window.electron.ipcRenderer.removeAllListeners('update-not-available')
      window.electron.ipcRenderer.removeAllListeners('download-progress')
      window.electron.ipcRenderer.removeAllListeners('update-downloaded')
      window.electron.ipcRenderer.removeAllListeners('update-error')
    }
  }, [])

  const handleDownloadUpdate = (): void => {
    window.logger.info('[UpdateButton] Download update requested')
    window.electron.ipcRenderer.send('download-update')
  }

  const handleInstallUpdate = (): void => {
    window.logger.info('[UpdateButton] Install update requested')
    window.electron.ipcRenderer.send('quit-and-install')
  }

  const handleUpdateAction = (): void => {
    if (updateStatus === 'available') {
      handleDownloadUpdate()
    } else if (updateStatus === 'downloaded') {
      handleInstallUpdate()
    }
  }

  const handleCheckForUpdates = (): void => {
    window.logger.info('[UpdateButton] Manual check for updates requested')
    window.electron.ipcRenderer.send('check-for-updates')
  }

  // Render different buttons based on update status
  switch (updateStatus) {
    case 'checking':
      return (
        <button
          disabled
          className="w-fit mx-auto flex items-center gap-2 justify-center px-3 py-1.5 text-xs text-zinc-400 bg-zinc-700/30 rounded-full border border-zinc-700"
        >
          <RefreshCw className="w-4 h-4 animate-spin" />
          Checking...
        </button>
      )

    case 'available':
      return (
        <button
          onClick={handleUpdateAction}
          className="w-fit mx-auto flex items-center gap-2 justify-center px-3 py-1.5 text-xs text-zinc-100 bg-zinc-700/30 rounded-full border border-zinc-700 hover:bg-zinc-700/50"
        >
          <HardDriveDownload className="w-4 h-4" />
          Update
        </button>
      )

    case 'downloading':
      return (
        <button
          disabled
          className="w-fit mx-auto flex items-center gap-2 justify-center px-3 py-1.5 text-xs text-zinc-400 bg-zinc-700/30 rounded-full border border-zinc-700"
        >
          <Download className="w-4 h-4 animate-pulse" />
          {updateProgress.toFixed(0)}%
        </button>
      )

    case 'downloaded':
      return (
        <button
          onClick={handleInstallUpdate}
          className="w-fit mx-auto flex items-center gap-2 justify-center px-3 py-1.5 text-xs text-zinc-100 bg-green-700/30 rounded-full border border-green-700 hover:bg-green-700/50"
        >
          <Check className="w-4 h-4" />
          Install
        </button>
      )

    case 'error':
      return (
        <button
          onClick={handleCheckForUpdates}
          title={updateError}
          className="w-fit mx-auto flex items-center gap-2 justify-center px-3 py-1.5 text-xs text-zinc-100 bg-red-700/30 rounded-full border border-red-700 hover:bg-red-700/50"
        >
          <X className="w-4 h-4" />
          Retry
        </button>
      )

    case 'not-available':
    default:
      return (
        <button
          onClick={handleCheckForUpdates}
          className="w-fit mx-auto flex items-center gap-2 justify-center px-3 py-1.5 text-xs text-zinc-100 bg-zinc-700/30 rounded-full border border-zinc-700 hover:bg-zinc-700/50"
        >
          <Check className="w-4 h-4" />
          All up to date
        </button>
      )
  }
}
