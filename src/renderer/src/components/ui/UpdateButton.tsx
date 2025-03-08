/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect } from 'react'
import { Download, X, Loader2 } from 'lucide-react'

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

  // Uncomment this to only show the button when relevant
  if (
    updateStatus !== 'available' &&
    updateStatus !== 'downloaded' &&
    updateStatus !== 'downloading' &&
    updateStatus !== 'error'
  ) {
    return null
  }

  return (
    <button
      onClick={handleUpdateAction}
      disabled={updateStatus === 'downloading'}
      className={`
        w-full px-4 py-2 rounded-lg flex items-center justify-between
        transition-all duration-200 relative overflow-hidden
        ${
          updateStatus === 'error'
            ? 'bg-red-500/20 text-red-300 hover:bg-red-500/30'
            : updateStatus === 'downloading'
              ? 'bg-zinc-700/30 text-zinc-400 cursor-wait'
              : updateStatus === 'downloaded'
                ? 'bg-green-500/20 text-green-300 hover:bg-green-500/30'
                : 'bg-blue-500/20 text-blue-300 hover:bg-blue-500/30'
        }
      `}
    >
      <div className="flex items-center gap-2">
        {updateStatus === 'downloading' ? (
          <Loader2 size={18} className="animate-spin" />
        ) : updateStatus === 'error' ? (
          <X size={18} className="text-red-300" />
        ) : (
          <Download size={18} />
        )}
        <span className="text-sm font-medium">
          {updateStatus === 'available'
            ? 'Update Available'
            : updateStatus === 'downloading'
              ? 'Downloading...'
              : updateStatus === 'downloaded'
                ? 'Install Update'
                : 'Update Error'}
        </span>
      </div>

      {/* Progress bar for downloading state */}
      {updateStatus === 'downloading' && (
        <div
          className="absolute bottom-0 left-0 h-0.5 bg-blue-500 transition-all duration-200"
          style={{ width: `${updateProgress}%` }}
        />
      )}

      {/* Show error message or progress percentage */}
      <span className="text-xs opacity-75">
        {updateStatus === 'error'
          ? updateError
          : updateStatus === 'downloading'
            ? `${Math.round(updateProgress)}%`
            : ''}
      </span>
    </button>
  )
}
