interface UpdateNotificationProps {
  status: 'checking' | 'available' | 'not-available' | 'downloading' | 'downloaded' | 'error'
  progress?: number
  error?: string
  onDownload?: () => void
  onInstall?: () => void
}

export function UpdateNotification({
  status,
  progress,
  error,
  onDownload,
  onInstall
}: UpdateNotificationProps) {
  if (status === 'not-available' || status === 'checking') return null

  return (
    <div className="fixed bottom-4 right-4 p-4 bg-white rounded-lg shadow-lg border border-gray-200 max-w-sm">
      {status === 'available' && (
        <div>
          <p className="text-sm mb-2">A new update is available!</p>
          <button onClick={onDownload}>Download Update</button>
        </div>
      )}

      {status === 'downloading' && (
        <div>
          <p className="text-sm mb-2">Downloading update: {Math.round(progress || 0)}%</p>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}

      {status === 'downloaded' && (
        <div>
          <p className="text-sm mb-2">Update ready to install!</p>
          <button onClick={onInstall}>Install and Restart</button>
        </div>
      )}

      {status === 'error' && (
        <div>
          <p className="text-sm text-red-600">Error updating: {error}</p>
        </div>
      )}
    </div>
  )
}
