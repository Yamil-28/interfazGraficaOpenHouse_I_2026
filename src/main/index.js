import { app, shell, BrowserWindow, ipcMain, dialog } from 'electron'
import path, { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'

// 1. Importamos spawn en la parte superior
import { spawn } from 'child_process'

// 2. Variable global para el servidor Python
let servidorPython = null 

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 900,
    height: 670,
    show: false,
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// 3. UN SOLO BLOQUE app.whenReady() PARA TODO
app.whenReady().then(() => {
  electronApp.setAppUserModelId('com.electron')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // Se crea la ventana UNA SOLA VEZ
  createWindow()

  // 4. Encendemos el Servidor Persistente de Python
  const rutaServidor = path.join(__dirname, '../../servidor.py')
  servidorPython = spawn('python', [rutaServidor])
  
  servidorPython.stdout.on('data', (data) => console.log(`Python: ${data}`))

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// --- GESTIÓN DE CIERRE ---
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('will-quit', () => {
  if (servidorPython) servidorPython.kill() // Matamos a Python al salir
})

// --- PUENTE DE COMUNICACIÓN CON REACT ---
ipcMain.handle('abrir-archivo', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [{ name: 'Archivos CSV o Texto', extensions: ['csv', 'txt'] }]
  })
  if (!canceled) {
    return filePaths[0]
  }
})