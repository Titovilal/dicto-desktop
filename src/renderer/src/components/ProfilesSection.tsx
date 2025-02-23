import { useState } from 'react'
import { Profile, StoreSchema } from '@/types/types'
import { DeleteDialog } from './DeleteProfileDialog'
import { LANGUAGES } from '@/lib/languages'
import { ProfileForm } from './ProfileForm'
import { Settings, Check, Trash2, Plus } from 'lucide-react'
import { AI_MODELS, getModelName } from '@/lib/models'

interface ProfilesSectionProps {
  profiles: Profile[]
  onAddProfile: (profile: Profile) => Promise<void>
  onUpdateProfile: (profile: Profile) => Promise<void>
  onDeleteProfile: (profile: Profile) => Promise<void>
  onSelectProfile: (profile: Profile) => Promise<void>
  settings: StoreSchema['settings'] | null
}

export function ProfilesSection({
  profiles,
  onAddProfile,
  onUpdateProfile,
  onDeleteProfile,
  onSelectProfile,
  settings
}: ProfilesSectionProps) {
  const [editingProfile, setEditingProfile] = useState<Profile | null>(null)
  const [newProfileName, setNewProfileName] = useState('')
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [profileToDelete, setProfileToDelete] = useState<Profile | null>(null)

  const handleAddProfile = async () => {
    if (!newProfileName.trim()) return

    const newProfile: Profile = {
      name: newProfileName,
      prompt: '',
      useAI: false,
      copyToClipboard: true,
      language: 'english',
      returnBoth: false,
      autoPaste: false,
      modelName: 'gemini-flash-2.0',
      temperature: 0.7,
      transcriptionPrompt: 'Transcribe the following audio:'
    }

    await onAddProfile(newProfile)
    setNewProfileName('')
  }

  const handleDeleteClick = (profile: Profile) => {
    setProfileToDelete(profile)
    setIsDeleteDialogOpen(true)
  }

  const handleConfirmDelete = async () => {
    if (!profileToDelete) return
    await onDeleteProfile(profileToDelete)
    setIsDeleteDialogOpen(false)
    setProfileToDelete(null)
  }

  const handleSelectProfile = async (profile: Profile) => {
    await onSelectProfile(profile)
  }

  const handleUpdateProfile = async (profile: Profile, updates: Profile) => {
    const updatedProfile = {
      ...updates,
      name: profile.name
    }
    await onUpdateProfile(updatedProfile)
    setEditingProfile(null)
  }

  if (editingProfile) {
    return (
      <section className="h-full flex flex-col">
        <ProfileForm
          profile={editingProfile}
          onCancel={() => setEditingProfile(null)}
          onSave={handleUpdateProfile}
        />
      </section>
    )
  }

  return (
    <section className="h-full flex flex-col">
      <div className="flex-1 overflow-y-auto pr-4 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-zinc-800/30 [&::-webkit-scrollbar-thumb]:bg-zinc-600/50 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:border-2 [&::-webkit-scrollbar-thumb]:border-zinc-800/30 hover:[&::-webkit-scrollbar-thumb]:bg-zinc-500/50">
        <div className="space-y-6">
          {/* Add Profile Section */}
          <div className="p-6 rounded-xl bg-gradient-to-br from-zinc-800/50 to-zinc-800/30 border border-zinc-700/30 backdrop-blur-sm">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-medium text-zinc-100">Profiles</h2>
              <div className="px-3 py-1 rounded-full bg-zinc-700/30 text-xs text-zinc-400">
                {profiles.length} profiles
              </div>
            </div>

            <div className="flex items-center gap-4">
              <input
                type="text"
                value={newProfileName}
                onChange={(e) => setNewProfileName(e.target.value)}
                placeholder="Enter profile name"
                className="flex-1 p-3 rounded-lg bg-zinc-800/50 border border-zinc-700/50 text-zinc-100 text-sm font-medium focus:outline-none focus:ring-1 focus:ring-zinc-600 transition-all duration-200 placeholder:text-zinc-600"
              />
              <button
                onClick={handleAddProfile}
                disabled={!newProfileName.trim()}
                className="p-3 rounded-lg bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Plus className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Profiles Grid */}
          <div className="grid grid-cols-1 gap-4">
            {profiles.map((profile) => (
              <div
                key={profile.name}
                className="p-6 rounded-xl bg-gradient-to-br from-zinc-800/50 to-zinc-800/30 border border-zinc-700/30 backdrop-blur-sm hover:from-zinc-800/60 hover:to-zinc-800/40 transition-all duration-200"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-medium text-zinc-100">{profile.name}</h3>
                      {settings?.selectedProfile === profile.name && (
                        <div className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 text-xs font-medium">
                          Active
                        </div>
                      )}
                    </div>
                    <p className="text-xs text-zinc-400">
                      {LANGUAGES[profile.language as keyof typeof LANGUAGES]}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    {settings?.selectedProfile !== profile.name && (
                      <button
                        onClick={() => handleSelectProfile(profile)}
                        className="p-2 rounded-lg bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30 transition-all duration-200"
                      >
                        <Check className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => setEditingProfile(profile)}
                      className="p-2 rounded-lg bg-zinc-700/50 text-zinc-300 hover:bg-zinc-700/70 transition-all duration-200"
                    >
                      <Settings className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteClick(profile)}
                      className="p-2 rounded-lg bg-red-500/20 text-red-500 hover:bg-red-500/30 transition-all duration-200"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Profile Features Grid */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="p-3 rounded-lg bg-zinc-800/30 border border-zinc-700/30">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-zinc-400">AI Processing</span>
                      <div
                        className={`w-2 h-2 rounded-full ${profile.useAI ? 'bg-emerald-500' : 'bg-zinc-600'}`}
                      />
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-800/30 border border-zinc-700/30">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-zinc-400">Auto Copy</span>
                      <div
                        className={`w-2 h-2 rounded-full ${profile.copyToClipboard ? 'bg-emerald-500' : 'bg-zinc-600'}`}
                      />
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-800/30 border border-zinc-700/30">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-zinc-400">Auto Paste</span>
                      <div
                        className={`w-2 h-2 rounded-full ${profile.autoPaste ? 'bg-emerald-500' : 'bg-zinc-600'}`}
                      />
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-800/30 border border-zinc-700/30">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-zinc-400">Return Both</span>
                      <div
                        className={`w-2 h-2 rounded-full ${profile.returnBoth ? 'bg-emerald-500' : 'bg-zinc-600'}`}
                      />
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-800/30 border border-zinc-700/30">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-zinc-400">Model</span>
                      <span className="text-xs text-zinc-300">
                        {getModelName(profile.modelName as keyof typeof AI_MODELS)}
                      </span>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-800/30 border border-zinc-700/30">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-zinc-400">Temperature</span>
                      <span className="text-xs text-zinc-300">
                        {profile.temperature.toFixed(1)}
                      </span>
                    </div>
                  </div>
                </div>

                {profile.transcriptionPrompt && (
                  <div className="p-3 rounded-lg bg-zinc-800/30 border border-zinc-700/30">
                    <span className="block text-xs text-zinc-400 mb-1">Transcription Prompt</span>
                    <p className="text-sm text-zinc-300 line-clamp-2">
                      {profile.transcriptionPrompt}
                    </p>
                  </div>
                )}

                {profile.prompt && (
                  <div className="p-3 rounded-lg bg-zinc-800/30 border border-zinc-700/30">
                    <span className="block text-xs text-zinc-400 mb-1">Prompt</span>
                    <p className="text-sm text-zinc-300 line-clamp-2">{profile.prompt}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <DeleteDialog
        isOpen={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        onConfirm={handleConfirmDelete}
        profileName={profileToDelete?.name || ''}
      />
    </section>
  )
}
