<script setup lang="ts">
import { ref, watch } from 'vue'
import type { AppState } from './types'
import { useOcrApi } from './composables/useOcrApi'
import { useDialogues } from './composables/useDialogues'
import FileLoader from './components/FileLoader.vue'
import ProgressBar from './components/ProgressBar.vue'
import DialogueList from './components/DialogueList.vue'
import CropPopup from './components/CropPopup.vue'
import SaveControls from './components/SaveControls.vue'

const appState = ref<AppState>('idle')
const showCrop = ref(false)
const cropImageUrl = ref('')
const videoPath = ref('')

const {
  phase, current, total,
  dialogues: ocrDialogues,
  isProcessing, error,
  startOcr, getCropUrl, deleteCrops,
} = useOcrApi()

const {
  dialogues, canUndoDelete, loadFromOcr,
  updateSpeaker, updateSpeakerAll, updateText,
  deleteDialogue, undoDelete,
  toJson, getDefaultSavePath, clear,
} = useDialogues()

// OCR 완료 감지 → editing 상태로 전환
watch(isProcessing, (processing, wasProcessing) => {
  if (wasProcessing && !processing && !error.value) {
    loadFromOcr(ocrDialogues.value, videoPath.value)
    appState.value = 'editing'
  }
})

async function handleFileSelected(path: string) {
  videoPath.value = path
  clear()
  appState.value = 'processing'
  await startOcr(path)
}

function handleClickDialogue(index: number) {
  const dialogue = dialogues.value.find((d) => d.index === index)
  if (dialogue) {
    cropImageUrl.value = getCropUrl(dialogue.cropFilename)
    showCrop.value = true
  }
}

async function handleSave(path: string) {
  const json = toJson()
  if (!json) return
  await window.electronAPI.writeFile(path, json)
}
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <h1>게임 대사 OCR 추출기</h1>
    </header>

    <main class="app-main">
      <!-- idle: 파일 선택 -->
      <div v-if="appState === 'idle'" class="center-content">
        <FileLoader @file-selected="handleFileSelected" />
      </div>

      <!-- processing: 진행률 표시 -->
      <div v-else-if="appState === 'processing'" class="center-content">
        <ProgressBar :phase="phase" :current="current" :total="total" />
        <p v-if="error" class="error-text">{{ error }}</p>
      </div>

      <!-- editing: 대사 편집 -->
      <div v-else-if="appState === 'editing'" class="editing-content">
        <div class="editing-toolbar">
          <FileLoader @file-selected="handleFileSelected" />
          <SaveControls
            :default-path="getDefaultSavePath()"
            @save="handleSave"
          />
        </div>

        <div class="editing-actions">
          <button
            v-if="canUndoDelete"
            class="undo-btn"
            @click="undoDelete"
          >
            삭제 취소
          </button>
        </div>

        <DialogueList
          :dialogues="dialogues"
          @update:speaker="updateSpeaker"
          @update:speaker-all="updateSpeakerAll"
          @update:text="updateText"
          @delete="deleteDialogue"
          @click-dialogue="handleClickDialogue"
        />
      </div>
    </main>

    <CropPopup
      :image-url="cropImageUrl"
      :visible="showCrop"
      @close="showCrop = false"
    />
  </div>
</template>

<style scoped>
.app-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.app-header {
  margin-bottom: 24px;
}

.app-header h1 {
  font-size: 22px;
  color: #333;
}

.center-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 80px;
  gap: 16px;
}

.editing-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.editing-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.editing-actions {
  display: flex;
  gap: 8px;
}

.undo-btn {
  padding: 4px 12px;
  font-size: 13px;
  background-color: #fff8e1;
  color: #f57f17;
  border: 1px solid #f57f17;
  border-radius: 4px;
  cursor: pointer;
}

.undo-btn:hover {
  background-color: #f57f17;
  color: #ffffff;
}

.error-text {
  color: #d32f2f;
  font-size: 14px;
}
</style>
