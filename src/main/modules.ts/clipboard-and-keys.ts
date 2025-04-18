import { clipboard } from 'electron'
import { keyboard, Key } from '@nut-tree-fork/nut-js'

export function getClipboardText(): string {
  console.log('[CLIPBOARD] Getting clipboard text')
  return clipboard.readText()
}

export function setClipboardText(text: string): void {
  console.log('[CLIPBOARD] Setting clipboard text')
  clipboard.writeText(text)
}

export async function simulateCopy(): Promise<void> {
  console.log('[CLIPBOARD] Simulating copy')
  try {
    await keyboard.pressKey(Key.LeftControl)
    await keyboard.pressKey(Key.C)
    await keyboard.releaseKey(Key.C)
    await keyboard.releaseKey(Key.LeftControl)
  } catch (error) {
    console.error('Error simulating copy:', error)
  }
}

export async function simulatePaste(): Promise<void> {
  console.log('[CLIPBOARD] Simulating paste')
  try {
    await keyboard.pressKey(Key.LeftControl)
    await keyboard.pressKey(Key.V)
    await keyboard.releaseKey(Key.V)
    await keyboard.releaseKey(Key.LeftControl)
  } catch (error) {
    console.error('Error simulating paste:', error)
  }
}

export async function simulateEnter(): Promise<void> {
  console.log('[CLIPBOARD] Simulating enter')
  try {
    await keyboard.pressKey(Key.Enter)
    await keyboard.releaseKey(Key.Enter)
  } catch (error) {
    console.error('Error simulating enter:', error)
  }
}
