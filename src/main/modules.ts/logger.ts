import log from 'electron-log'
import { ipcMain } from 'electron'

// Configure electron-log
// By default it writes logs to the following locations:
// on Linux: ~/.config/{app name}/logs/{process type}.log
// on macOS: ~/Library/Logs/{app name}/{process type}.log
// on Windows: %USERPROFILE%\AppData\Roaming\{app name}\logs\{process type}.log

export function initLogger(): void {
  // Set custom log file path if needed
  // log.transports.file.resolvePath = () => path.join(app.getPath('userData'), 'logs/main.log');

  // Configure log level
  log.transports.file.level = 'info'
  log.transports.console.level = 'debug'

  // Configure log format
  log.transports.file.format = '[{y}-{m}-{d} {h}:{i}:{s}.{ms}] [{level}] {text}'

  // Set max log file size (default: 1MB)
  log.transports.file.maxSize = 5 * 1024 * 1024

  // Forward console logs to electron-log
  console.log = log.log
  console.error = log.error
  console.warn = log.warn
  console.info = log.info
  console.debug = log.debug

  log.info('Logger initialized')
  log.info(`Log file location: ${log.transports.file.getFile().path}`)
}

export function initLoggerIPC(): void {
  ipcMain.on('log', (_, { level, message }) => {
    switch (level) {
      case 'info':
        log.info(message)
        break
      case 'warn':
        log.warn(message)
        break
      case 'error':
        log.error(message)
        break
      case 'debug':
        log.debug(message)
        break
      default:
        log.info(message)
    }
  })

  log.info('Logger IPC initialized')
}

export default log
