import { useState } from 'react'
import { Profile, StoreSchema } from '@/types/types'
import { DeleteDialog } from './DeleteProfileDialog'
import { LANGUAGES } from '@/lib/languages'
import { ProfileForm } from './ProfileForm'
import { Settings, Check, Trash2, Plus } from 'lucide-react'
import { AI_MODELS } from '@/lib/models'
import { getNewProfileTemplate } from '@/lib/profile-template'

interface ProfilesSectionProps {
  profiles: Profile[]
  onAddProfile: (profile: Profile) => Promise<void>
  onUpdateProfile: (profile: Profile) => Promise<void>
  onDeleteProfile: (profile: Profile) => Promise<void>
  onSelectProfile: (profile: Profile) => Promise<void>
  settings: StoreSchema['settings'] | null
}

// Añade este componente para los indicadores
function FeatureIndicator({ enabled, label }: { enabled: boolean; label: string }): JSX.Element {
  return (
    <div className="flex items-center gap-1.5">
      <div className={`w-1.5 h-1.5 rounded-full ${enabled ? 'bg-emerald-500' : 'bg-zinc-600'}`} />
      <span className="text-xs text-zinc-400">{label}</span>
    </div>
  )
}

export function ProfilesSection({
  profiles,
  onAddProfile,
  onUpdateProfile,
  onDeleteProfile,
  onSelectProfile,
  settings
}: ProfilesSectionProps): JSX.Element {
  const [editingProfile, setEditingProfile] = useState<Profile | null>(null)
  const [newProfileName, setNewProfileName] = useState('')
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [profileToDelete, setProfileToDelete] = useState<Profile | null>(null)

  const handleAddProfile = async (): Promise<void> => {
    if (!newProfileName.trim()) return
    const newProfile = getNewProfileTemplate(newProfileName)
    await onAddProfile(newProfile)
    setNewProfileName('')
  }

  const handleDeleteClick = (profile: Profile): void => {
    setProfileToDelete(profile)
    setIsDeleteDialogOpen(true)
  }

  const handleConfirmDelete = async (): Promise<void> => {
    if (!profileToDelete) return
    await onDeleteProfile(profileToDelete)
    setIsDeleteDialogOpen(false)
    setProfileToDelete(null)
  }

  const handleSelectProfile = async (profile: Profile): Promise<void> => {
    await onSelectProfile(profile)
  }

  const handleUpdateProfile = async (profile: Profile, updates: Profile): Promise<void> => {
    const updatedProfile = {
      ...updates,
      name: profile.name
    }
    await onUpdateProfile(updatedProfile)
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
                className={`p-4 rounded-xl backdrop-blur-sm transition-all duration-200 ${
                  profile.onlyLlm
                    ? 'bg-gradient-to-br from-zinc-800/50 to-zinc-800/30 border border-zinc-700/30 hover:from-zinc-800/60 hover:to-zinc-800/40'
                    : 'bg-gradient-to-br from-zinc-800/50 to-zinc-800/30 border border-zinc-700/30 hover:from-zinc-800/60 hover:to-zinc-800/40'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3
                          className={
                            settings?.selectedProfile !== profile.name
                              ? 'text-base font-medium text-zinc-100'
                              : 'text-base font-medium text-emerald-500'
                          }
                        >
                          {profile.name}
                        </h3>
                        {profile.onlyLlm && (
                          <div className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 text-xs font-medium border border-blue-500/20">
                            Direct LLM
                          </div>
                        )}
                      </div>
                      {!profile.onlyLlm && (
                        <div className="flex items-center gap-3 mt-1">
                          <span className="text-xs text-zinc-400">
                            {LANGUAGES[profile.language as keyof typeof LANGUAGES]}
                          </span>
                          <span className="text-xs text-zinc-500">•</span>
                          <span className="text-xs text-zinc-400">
                            {AI_MODELS[profile.modelName as keyof typeof AI_MODELS]}
                          </span>
                        </div>
                      )}
                      {profile.onlyLlm && (
                        <span className="text-xs text-zinc-400">
                          {AI_MODELS[profile.modelName as keyof typeof AI_MODELS]}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {profile.onlyLlm ? (
                      <div className="grid grid-cols-3 gap-x-3 gap-y-1 mr-2">
                        <FeatureIndicator enabled={true} label="Copy" />
                        <FeatureIndicator enabled={true} label="Paste" />
                        <FeatureIndicator enabled={false} label="Enter" />
                        <FeatureIndicator enabled={true} label="Use AI" />
                        <FeatureIndicator enabled={true} label="Selected Text" />
                      </div>
                    ) : (
                      <div className="grid grid-cols-3 gap-x-3 gap-y-1 mr-2">
                        <FeatureIndicator enabled={profile.copyToClipboard} label="Copy" />
                        <FeatureIndicator enabled={profile.autoPaste} label="Paste" />
                        <FeatureIndicator enabled={profile.autoEnter} label="Enter" />
                        <FeatureIndicator enabled={profile.useAI} label="Use AI" />
                        <FeatureIndicator enabled={profile.useSelectedText} label="Selected Text" />
                      </div>
                    )}

                    <button
                      onClick={() => handleSelectProfile(profile)}
                      className={`p-2 rounded-lg ${
                        settings?.selectedProfile !== profile.name
                          ? 'text-zinc-300 hover:bg-zinc-700/70 transition-all duration-200'
                          : 'text-emerald-500 transition-all duration-200'
                      }`}
                    >
                      <Check className="w-4 h-4" />
                    </button>

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
