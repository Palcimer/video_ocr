<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Dialogue } from '../types'

const MIN_ROWS = 1
const MAX_ROWS = 10

const props = defineProps<{
  dialogue: Dialogue
}>()

const textRows = computed(() => {
  const lineCount = props.dialogue.text.split('\n').length
  return Math.max(MIN_ROWS, Math.min(lineCount + 1, MAX_ROWS))
})

const emit = defineEmits<{
  'update:speaker': [index: number, value: string]
  'update:text': [index: number, value: string]
  'update:speakerAll': [oldName: string, newName: string]
  delete: [index: number]
  click: [index: number]
}>()

const originalSpeaker = ref(props.dialogue.speaker)

function handleSpeakerInput(value: string) {
  emit('update:speaker', props.dialogue.index, value)
}

function handleApplyAll() {
  emit('update:speakerAll', originalSpeaker.value, props.dialogue.speaker)
  originalSpeaker.value = props.dialogue.speaker
}
</script>

<template>
  <div class="dialogue-item" @click="emit('click', dialogue.index)">
    <div class="dialogue-header">
      <span class="dialogue-index">#{{ dialogue.index + 1 }}</span>
      <input
        class="speaker-input"
        :value="dialogue.speaker"
        placeholder="화자명"
        @input="handleSpeakerInput(($event.target as HTMLInputElement).value)"
        @click.stop
      />
      <button
        v-if="dialogue.speaker !== originalSpeaker"
        class="apply-all-btn"
        title="같은 화자명 전체 변경"
        @click.stop="handleApplyAll"
      >
        전체 적용
      </button>
      <button
        class="delete-btn"
        title="이 대사 삭제"
        @click.stop="emit('delete', dialogue.index)"
      >
        삭제
      </button>
    </div>
    <textarea
      class="text-input"
      :value="dialogue.text"
      placeholder="대사"
      :rows="textRows"
      @input="emit('update:text', dialogue.index, ($event.target as HTMLTextAreaElement).value)"
      @click.stop
    />
  </div>
</template>

<style scoped>
.dialogue-item {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.15s;
}

.dialogue-item:hover {
  background-color: #f5f8fc;
}

.dialogue-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.dialogue-index {
  font-size: 12px;
  color: #999;
  min-width: 28px;
}

.apply-all-btn {
  padding: 2px 8px;
  font-size: 12px;
  background-color: #eef4fb;
  color: #4a90d9;
  border: 1px solid #4a90d9;
  border-radius: 4px;
  cursor: pointer;
  white-space: nowrap;
}

.apply-all-btn:hover {
  background-color: #4a90d9;
  color: #ffffff;
}

.delete-btn {
  padding: 2px 8px;
  font-size: 12px;
  background-color: #fef2f2;
  color: #d32f2f;
  border: 1px solid #d32f2f;
  border-radius: 4px;
  cursor: pointer;
  white-space: nowrap;
}

.delete-btn:hover {
  background-color: #d32f2f;
  color: #ffffff;
}

.speaker-input {
  flex: 1;
  padding: 4px 8px;
  font-size: 14px;
  font-weight: 600;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.text-input {
  width: 100%;
  padding: 6px 8px;
  font-size: 14px;
  border: 1px solid #ccc;
  border-radius: 4px;
  resize: vertical;
  font-family: inherit;
}
</style>
