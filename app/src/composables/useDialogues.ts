import { ref } from 'vue'
import type { Dialogue, DialogueExport } from '../types'

const dialogues = ref<Dialogue[]>([])
const videoPath = ref<string | null>(null)

function loadFromOcr(results: Dialogue[], path: string) {
  dialogues.value = results
  videoPath.value = path
}

function updateSpeaker(index: number, value: string) {
  dialogues.value[index].speaker = value
}

function updateText(index: number, value: string) {
  dialogues.value[index].text = value
}

function toJson(): string {
  if (!videoPath.value) return ''

  const filename = videoPath.value.split('/').pop()?.split('\\').pop() ?? ''
  const exportData: DialogueExport = {
    source: filename,
    dialogues: dialogues.value.map((d) => ({
      speaker: d.speaker,
      text: d.text,
    })),
  }
  return JSON.stringify(exportData, null, 2)
}

function getDefaultSavePath(): string {
  if (!videoPath.value) return 'output.json'
  return videoPath.value.replace(/\.mp4$/i, '.json')
}

function clear() {
  dialogues.value = []
  videoPath.value = null
}

export function useDialogues() {
  return {
    dialogues,
    videoPath,
    loadFromOcr,
    updateSpeaker,
    updateText,
    toJson,
    getDefaultSavePath,
    clear,
  }
}
