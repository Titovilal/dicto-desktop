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
      label: 'Sounds',
      type: 'checkbox',
      checked: true,
      click: (menuItem) => {
        mainWindow?.webContents.send('sound-enabled-changed', menuItem.checked)
      }
    },
    {
      label: 'Always Visible',
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
      label: 'Exit',
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

export function updateSoundMenuItem(value) {
  if (tray && trayContextMenu) {
    const soundMenuItem = trayContextMenu.items.find((item) => item.label === 'Sounds')
    if (soundMenuItem) {
      soundMenuItem.checked = value
      tray.setContextMenu(trayContextMenu)
    }
  }
}
