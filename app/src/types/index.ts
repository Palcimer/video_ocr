/** 앱 상태 */
export type AppState = 'idle' | 'processing' | 'editing'

/** OCR 진행 단계 */
export type OcrPhase = 'scan' | 'ocr'

/** 단일 대사 */
export interface Dialogue {
  index: number
  speaker: string
  text: string
  cropFilename: string
}

/** SSE 진행률 이벤트 */
export interface OcrProgressEvent {
  phase: OcrPhase
  current: number
  total: number
  dialogue: Dialogue | null
}

/** JSON 출력 포맷 */
export interface DialogueExport {
  source: string
  dialogues: {
    speaker: string
    text: string
  }[]
}
