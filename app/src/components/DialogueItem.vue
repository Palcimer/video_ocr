<script setup lang="ts">
import type { Dialogue } from '../types'

defineProps<{
  dialogue: Dialogue
}>()

const emit = defineEmits<{
  'update:speaker': [index: number, value: string]
  'update:text': [index: number, value: string]
  click: [index: number]
}>()
</script>

<template>
  <div class="dialogue-item" @click="emit('click', dialogue.index)">
    <div class="dialogue-header">
      <span class="dialogue-index">#{{ dialogue.index + 1 }}</span>
      <input
        class="speaker-input"
        :value="dialogue.speaker"
        placeholder="화자명"
        @input="emit('update:speaker', dialogue.index, ($event.target as HTMLInputElement).value)"
        @click.stop
      />
    </div>
    <textarea
      class="text-input"
      :value="dialogue.text"
      placeholder="대사"
      rows="2"
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
