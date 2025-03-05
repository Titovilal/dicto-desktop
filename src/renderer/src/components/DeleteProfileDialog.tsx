interface DeleteDialogProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  profileName: string
}

export function DeleteDialog({
  isOpen,
  onClose,
  onConfirm,
  profileName
}: DeleteDialogProps): JSX.Element | null {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 w-[400px] shadow-lg">
        <h2 className="text-xl font-semibold text-zinc-100 mb-2">Delete Profile</h2>
        <p className="text-zinc-400 mb-6">
          Are you sure you want to delete the profile &quot;{profileName}&quot;? This action cannot
          be undone.
        </p>

        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 transition-all duration-200"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 rounded-lg bg-red-500/20 text-red-500 hover:bg-red-500/30 transition-all duration-200"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}
