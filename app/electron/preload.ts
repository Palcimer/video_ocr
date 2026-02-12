import { ipcRenderer, contextBridge } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  getServerPort: (): Promise<number | null> => {
    return ipcRenderer.invoke('get-server-port')
  },
  openVideoDialog: (): Promise<string | null> => {
    return ipcRenderer.invoke('open-video-dialog')
  },
  saveFileDialog: (defaultName: string): Promise<string | null> => {
    return ipcRenderer.invoke('save-file-dialog', defaultName)
  },
  writeFile: (filePath: string, content: string): Promise<boolean> => {
    return ipcRenderer.invoke('write-file', filePath, content)
  },
})
