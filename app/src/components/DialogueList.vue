<script setup lang="ts">
import type { Dialogue } from '../types'
import DialogueItem from './DialogueItem.vue'

defineProps<{
  dialogues: Dialogue[]
}>()

const emit = defineEmits<{
  'update:speaker': [index: number, value: string]
  'update:speakerAll': [oldName: string, newName: string]
  'update:text': [index: number, value: string]
  delete: [index: number]
  clickDialogue: [index: number]
}>()
</script>

<template>
  <div class="dialogue-list">
    <DialogueItem
      v-for="dialogue in dialogues"
      :key="dialogue.index"
      :dialogue="dialogue"
      @update:speaker="(i, v) => emit('update:speaker', i, v)"
      @update:speaker-all="(old, val) => emit('update:speakerAll', old, val)"
      @update:text="(i, v) => emit('update:text', i, v)"
      @delete="(i) => emit('delete', i)"
      @click="(i) => emit('clickDialogue', i)"
    />
  </div>
</template>

<style scoped>
.dialogue-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
