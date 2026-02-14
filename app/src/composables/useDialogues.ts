import { ref, computed } from 'vue'
import type { Dialogue, DialogueExport } from '../types'

interface DeletedEntry {
  dialogue: Dialogue
  position: number
}

const dialogues = ref<Dialogue[]>([])
const videoPath = ref<string | null>(null)
const deletedStack = ref<DeletedEntry[]>([])

const canUndoDelete = computed(() => deletedStack.value.length > 0)

function loadFromOcr(results: Dialogue[], path: string) {
  dialogues.value = results
  videoPath.value = path
  deletedStack.value = []
}

function updateSpeaker(index: number, value: string) {
  const d = dialogues.value.find((d) => d.index === index)
  if (d) d.speaker = value
}

function updateSpeakerAll(oldName: string, newName: string) {
  for (const dialogue of dialogues.value) {
    if (dialogue.speaker === oldName) {
      dialogue.speaker = newName
    }
  }
}

function updateText(index: number, value: string) {
  const d = dialogues.value.find((d) => d.index === index)
  if (d) d.text = value
}

function deleteDialogue(index: number) {
  const pos = dialogues.value.findIndex((d) => d.index === index)
  if (pos === -1) return
  const [removed] = dialogues.value.splice(pos, 1)
  deletedStack.value.push({ dialogue: removed, position: pos })
}

function undoDelete() {
  const entry = deletedStack.value.pop()
  if (!entry) return
  dialogues.value.splice(entry.position, 0, entry.dialogue)
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
  deletedStack.value = []
}

export function useDialogues() {
  return {
    dialogues,
    videoPath,
    canUndoDelete,
    loadFromOcr,
    updateSpeaker,
    updateSpeakerAll,
    updateText,
    deleteDialogue,
    undoDelete,
    toJson,
    getDefaultSavePath,
    clear,
  }
}
