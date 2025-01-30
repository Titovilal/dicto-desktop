import { ipcMain, clipboard } from 'electron'
import { updateSoundMenuItem } from './tray'
import {
	startShortcutRecording,
	stopShortcutRecording,
	registerGlobalShortcuts,
	handleKeyboardEvent,
	getCurrentShortcut
} from './shortcuts'
import {
	saveShortcut,
	loadShortcut,
	getProfiles,
	createProfile,
	updateProfile,
	deleteProfile,
	saveSelectedProfile,
	getSelectedProfile
} from './store'
import { processWithAI } from './ai.js'

export function setupIPC(mainWindow) {
	// Test IPC
	ipcMain.on('ping', () => console.log('pong'))

	// Always on top
	ipcMain.on('set-always-on-top', (_, value) => {
		if (mainWindow) {
			mainWindow.setAlwaysOnTop(value)
			mainWindow.webContents.send('always-on-top-changed', mainWindow.isAlwaysOnTop())
		}
	})

	// Sound settings
	ipcMain.on('set-sound-enabled', (_, value) => {
		updateSoundMenuItem(value)
	})

	// Shortcut recording
	ipcMain.on('start-shortcut-recording', () => {
		startShortcutRecording()
	})

	ipcMain.on('stop-shortcut-recording', () => {
		stopShortcutRecording()
		registerGlobalShortcuts(mainWindow)
	})

	// Keyboard event handling for shortcuts
	if (mainWindow) {
		mainWindow.webContents.on('before-input-event', (event, input) => {
			const newShortcut = handleKeyboardEvent(input)
			if (newShortcut) {
				mainWindow.webContents.send('shortcut-recorded', newShortcut)
				stopShortcutRecording()
				registerGlobalShortcuts(mainWindow)
			}
		})
	}

	// Always on top sync
	mainWindow.on('always-on-top-changed', (event, isOnTop) => {
		mainWindow.webContents.send('always-on-top-changed', isOnTop)
	})

	// Get current shortcut
	ipcMain.on('get-current-shortcut', () => {
		if (mainWindow) {
			const currentShortcut = getCurrentShortcut()
			mainWindow.webContents.send('current-shortcut', currentShortcut)
		}
	})

	ipcMain.handle('save-shortcut', async (event, shortcut) => {
		await saveShortcut(shortcut)
	})

	ipcMain.handle('load-shortcut', async () => {
		return await loadShortcut()
	})

	ipcMain.handle('get-profiles', async () => {
		return await getProfiles()
	})

	ipcMain.handle('create-profile', async (event, profile) => {
		await createProfile(profile)
	})

	ipcMain.handle('update-profile', async (event, profile) => {
		await updateProfile(profile)
	})

	ipcMain.handle('delete-profile', async (event, name) => {
		await deleteProfile(name)
	})

	ipcMain.handle('save-selected-profile', async (event, profileName) => {
		await saveSelectedProfile(profileName)
	})

	ipcMain.handle('get-selected-profile', async () => {
		return await getSelectedProfile()
	})

	ipcMain.handle('process-with-ai', async (event, { text, prompt }) => {
		return await processWithAI(text, prompt)
	})

	ipcMain.handle('write-to-clipboard', async (event, text) => {
		clipboard.writeText(text)
		return true
	})
}
