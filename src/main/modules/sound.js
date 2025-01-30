import { app } from 'electron'
import path from 'path'
import sound from 'sound-play'

const soundsPath = app.isPackaged
	? path.join(process.resourcesPath, 'sounds')
	: path.join(__dirname, '../../resources/sounds')

const sounds = {
	start: path.join(soundsPath, 'start-recording.mp3'),
	stop: path.join(soundsPath, 'stop-recording.mp3'),
	finish: path.join(soundsPath, 'finish-processing.mp3')
}

export async function playSound(soundName) {
	console.log(sounds)
	if (!sounds[soundName]) return
	try {
		await sound.play(sounds[soundName])
	} catch (error) {
		console.error(`Error playing ${soundName} sound:`, error)
	}
}
