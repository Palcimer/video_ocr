/// <reference types="vite-plugin-electron/electron-env" />

declare namespace NodeJS {
  interface ProcessEnv {
    APP_ROOT: string
    VITE_PUBLIC: string
  }
}

interface ElectronAPI {
  getServerPort: () => Promise<number | null>
  openVideoDialog: () => Promise<string | null>
  saveFileDialog: (defaultName: string) => Promise<string | null>
  writeFile: (filePath: string, content: string) => Promise<boolean>
}

interface Window {
  electronAPI: ElectronAPI
}
