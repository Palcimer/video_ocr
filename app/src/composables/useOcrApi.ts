import { ref } from 'vue'
import type { Dialogue, OcrPhase, OcrProgressEvent } from '../types'

const phase = ref<OcrPhase>('scan')
const current = ref(0)
const total = ref(0)
const dialogues = ref<Dialogue[]>([])
const isProcessing = ref(false)
const error = ref<string | null>(null)
const jobId = ref<string | null>(null)

let baseUrl = ''

async function ensureBaseUrl(): Promise<string> {
  if (baseUrl) return baseUrl
  const port = await window.electronAPI.getServerPort()
  if (!port) throw new Error('서버 포트를 가져올 수 없습니다')
  baseUrl = `http://127.0.0.1:${port}`
  return baseUrl
}

function parseDialogue(raw: Record<string, unknown>): Dialogue {
  return {
    index: raw.index as number,
    speaker: raw.speaker as string,
    text: raw.text as string,
    cropFilename: raw.crop_filename as string,
  }
}

function resetState() {
  phase.value = 'scan'
  current.value = 0
  total.value = 0
  dialogues.value = []
  error.value = null
  jobId.value = null
}

async function startOcr(videoPath: string, lang: string = 'kor') {
  const url = await ensureBaseUrl()
  await deleteCrops()  // 이전 작업 크롭 정리
  resetState()
  isProcessing.value = true

  try {
    // OCR 시작 요청
    const res = await fetch(`${url}/ocr/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ video_path: videoPath, lang }),
    })

    if (!res.ok) {
      const detail = await res.text()
      error.value = `OCR 시작 실패: ${detail}`
      isProcessing.value = false
      return
    }

    const data = await res.json()
    jobId.value = data.job_id

    // SSE 진행률 수신
    listenProgress(url, data.job_id)
  } catch (e) {
    error.value = `서버 연결 실패: ${e instanceof Error ? e.message : e}`
    isProcessing.value = false
  }
}

function listenProgress(url: string, id: string) {
  const source = new EventSource(`${url}/ocr/progress/${id}`)

  source.addEventListener('progress', (e: MessageEvent) => {
    const event: OcrProgressEvent = JSON.parse(e.data)
    phase.value = event.phase
    current.value = event.current
    total.value = event.total
    if (event.dialogue) {
      dialogues.value.push(parseDialogue(event.dialogue as unknown as Record<string, unknown>))
    }
  })

  source.addEventListener('complete', (e: MessageEvent) => {
    const rawList: Record<string, unknown>[] = JSON.parse(e.data)
    dialogues.value = rawList.map(parseDialogue)
    isProcessing.value = false
    source.close()
  })

  source.addEventListener('error', (e: Event) => {
    const messageEvent = e as MessageEvent
    error.value = messageEvent.data ?? 'SSE 연결 오류'
    isProcessing.value = false
    source.close()
  })
}

function getCropUrl(filename: string): string {
  if (!jobId.value) return ''
  return `${baseUrl}/ocr/crops/${jobId.value}/${filename}`
}

async function deleteCrops(): Promise<void> {
  if (!jobId.value) return
  const url = await ensureBaseUrl()
  await fetch(`${url}/ocr/crops/${jobId.value}`, { method: 'DELETE' })
  jobId.value = null
}

export function useOcrApi() {
  return {
    phase,
    current,
    total,
    dialogues,
    isProcessing,
    error,
    jobId,
    startOcr,
    getCropUrl,
    deleteCrops,
  }
}
