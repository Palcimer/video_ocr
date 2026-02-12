/**
 * FastAPI 서브프로세스 관리.
 * Python 서버를 spawn하고, 준비 상태를 확인하며, 종료를 관리한다.
 */

import { spawn, type ChildProcess } from 'node:child_process'
import http from 'node:http'
import path from 'node:path'
import net from 'node:net'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

const HEALTH_POLL_INTERVAL_MS = 200
const HEALTH_TIMEOUT_MS = 15_000
const SHUTDOWN_GRACE_MS = 3_000
const PROJECT_ROOT = path.join(__dirname, '..', '..')

let serverProcess: ChildProcess | null = null
let serverPort: number | null = null


// 현재 서버 포트 조회
export function getServerPort(): number | null {
  return serverPort
}

// 빈 TCP 포트 탐색(충돌 방지)
async function findFreePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const server = net.createServer()
    server.listen(0, '127.0.0.1', () => {
      const addr = server.address()
      if (addr && typeof addr === 'object') {
        const port = addr.port
        server.close(() => resolve(port))
      } else {
        server.close(() => reject(new Error('포트를 찾을 수 없습니다')))
      }
    })
    server.on('error', reject)
  })
}

// 서버 상태 확인
function healthCheck(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const req = http.get(`http://127.0.0.1:${port}/health`, (res) => {
      resolve(res.statusCode === 200)
    })
    req.on('error', () => resolve(false))
    req.setTimeout(1000, () => {
      req.destroy()
      resolve(false)
    })
  })
}

// 200ms 간격 폴링, 15초 타임아웃
async function waitForReady(port: number): Promise<void> {
  const deadline = Date.now() + HEALTH_TIMEOUT_MS

  while (Date.now() < deadline) {
    const ok = await healthCheck(port)
    if (ok) return

    await new Promise((r) => setTimeout(r, HEALTH_POLL_INTERVAL_MS))
  }

  throw new Error(`FastAPI 서버가 ${HEALTH_TIMEOUT_MS}ms 내에 응답하지 않습니다`)
}

// uvicorn spawn → 준비 대기 → 포트 반환
export async function startServer(): Promise<number> {
  const port = await findFreePort()

  const proc = spawn('python', [
    '-m', 'uvicorn', 'backend.server:app',
    '--host', '127.0.0.1',
    '--port', String(port),
    '--log-level', 'warning',
  ], {
    cwd: PROJECT_ROOT,
    stdio: ['ignore', 'pipe', 'pipe'],
  })

  proc.stdout?.on('data', (data: Buffer) => {
    console.log('[FastAPI]', data.toString().trim())
  })
  proc.stderr?.on('data', (data: Buffer) => {
    console.error('[FastAPI]', data.toString().trim())
  })
  proc.on('exit', (code) => {
    console.log(`[FastAPI] 프로세스 종료 (code: ${code})`)
    serverProcess = null
  })

  serverProcess = proc
  serverPort = port

  await waitForReady(port)
  console.log(`[FastAPI] 서버 준비 완료 (port: ${port})`)

  return port
}

// SIGTERM → 3초 대기 → 필요 시 SIGKILL 
export async function stopServer(): Promise<void> {
  if (!serverProcess) return

  const proc = serverProcess
  serverProcess = null
  serverPort = null

  proc.kill('SIGTERM')

  const exited = await new Promise<boolean>((resolve) => {
    const timer = setTimeout(() => resolve(false), SHUTDOWN_GRACE_MS)
    proc.on('exit', () => {
      clearTimeout(timer)
      resolve(true)
    })
  })

  if (!exited) {
    console.warn('[FastAPI] 정상 종료 실패, SIGKILL 전송')
    proc.kill('SIGKILL')
  }
}
