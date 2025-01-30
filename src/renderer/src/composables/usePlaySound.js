import { ref } from 'vue'

export function usePlaySound() {
	const soundEnabled = ref(true)

	const playSound = async (soundName) => {
		if (!soundEnabled.value) return
		await window.electron.ipcRenderer.invoke('play-sound', soundName)
	}

	const playStartSound = () => playSound('start')
	const playStopSound = () => playSound('stop')
	const playFinishSound = () => playSound('finish')

	return {
		soundEnabled,
		playStartSound,
		playStopSound,
		playFinishSound
	}
}
