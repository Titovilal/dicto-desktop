import { ref } from 'vue'

export function usePlaySound() {
	const soundEnabled = ref(true)
	const startSound = new Audio('/src/assets/start-recording.mp3')
	const stopSound = new Audio('/src/assets/stop-recording.mp3')
	const finishSound = new Audio('/src/assets/finish-processing.mp3')

	const playSoundClient = (sound) => {
		if (soundEnabled.value) {
			sound.play().catch((error) => {
				console.error('Error playing sound:', error)
			})
		}
	}
	const playStartSound = () => playSoundClient(startSound)
	const playStopSound = () => playSoundClient(stopSound)
	const playFinishSound = () => playSoundClient(finishSound)

	return {
		soundEnabled,
		playStartSound,
		playStopSound,
		playFinishSound
	}
}
