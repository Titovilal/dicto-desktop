import { Tray, Menu } from 'electron'
import icon from '../../../resources/icon.png?asset'

let tray = null
let trayContextMenu = null

export function createTray({ mainWindow, app }) {
  tray = new Tray(icon)
  trayContextMenu = Menu.buildFromTemplate([
    {
      label: 'Mostrar App',
      click: () => {
        mainWindow.show()
      }
    },
    {
      label: 'Sonidos',
      type: 'checkbox',
      checked: true,
      click: (menuItem) => {
        mainWindow?.webContents.send('sound-enabled-changed', menuItem.checked)
      }
    },
    {
      label: 'Siempre Visible',
      type: 'checkbox',
      checked: false,
      click: (menuItem) => {
        mainWindow.setAlwaysOnTop(menuItem.checked)
      }
    },
    {
      type: 'separator'
    },
    {
      label: 'Salir',
      click: () => {
        app.isQuitting = true
        app.quit()
      }
    }
  ])

  tray.setToolTip('Dicto Desktop')
  tray.setContextMenu(trayContextMenu)

  // Doble clic en el icono del tray muestra la app
  tray.on('double-click', () => {
    mainWindow.show()
  })

  return { tray, trayContextMenu }
}

export function updateTrayTooltip(isRecording) {
  if (isRecording) {
    tray?.setToolTip('Dicto Desktop - Grabando...')
  } else {
    tray?.setToolTip('Dicto Desktop')
  }
}

export function updateSoundMenuItem(value) {
  if (tray && trayContextMenu) {
    const soundMenuItem = trayContextMenu.items.find((item) => item.label === 'Sonidos')
    if (soundMenuItem) {
      soundMenuItem.checked = value
      tray.setContextMenu(trayContextMenu)
    }
  }
}
