import { app, BrowserWindow, dialog, ipcMain } from 'electron'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import fs from 'node:fs'
import { startServer, stopServer, getServerPort } from './python-server'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

process.env.APP_ROOT = path.join(__dirname, '..')

export const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL']
export const MAIN_DIST = path.join(process.env.APP_ROOT, 'dist-electron')
export const RENDERER_DIST = path.join(process.env.APP_ROOT, 'dist')

process.env.VITE_PUBLIC = VITE_DEV_SERVER_URL
  ? path.join(process.env.APP_ROOT, 'public')
  : RENDERER_DIST

let win: BrowserWindow | null

function createWindow() {
  win = new BrowserWindow({
    width: 1000,
    height: 750,
    backgroundColor: '#ffffff',
    webPreferences: {
      preload: path.join(__dirname, 'preload.mjs'),
    },
  })

  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL)
  } else {
    win.loadFile(path.join(RENDERER_DIST, 'index.html'))
  }
}

// --- IPC 핸들러 ---

ipcMain.handle('get-server-port', () => {
  return getServerPort()
})

ipcMain.handle('open-video-dialog', async () => {
  if (!win) return null
  const result = await dialog.showOpenDialog(win, {
    title: '영상 파일 선택',
    filters: [{ name: 'MP4 Video', extensions: ['mp4'] }],
    properties: ['openFile'],
  })
  if (result.canceled || result.filePaths.length === 0) return null
  return result.filePaths[0]
})

ipcMain.handle('save-file-dialog', async (_event, defaultName: string) => {
  if (!win) return null
  const result = await dialog.showSaveDialog(win, {
    title: '다른 이름으로 저장',
    defaultPath: defaultName,
    filters: [{ name: 'JSON', extensions: ['json'] }],
  })
  if (result.canceled || !result.filePath) return null
  return result.filePath
})

ipcMain.handle('write-file', async (_event, filePath: string, content: string) => {
  fs.writeFileSync(filePath, content, 'utf-8')
  return true
})

// --- 앱 생명주기 ---

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
    win = null
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

app.whenReady().then(async () => {
  try {
    await startServer()
    createWindow()
  } catch (err) {
    dialog.showErrorBox(
      'FastAPI 서버 오류',
      `서버를 시작할 수 없습니다:\n${err}`,
    )
    app.quit()
  }
})

app.on('before-quit', async () => {
  await stopServer()
})
