<script setup lang="ts">
const emit = defineEmits<{
  save: [path: string]
}>()

const props = defineProps<{
  defaultPath: string
}>()

async function handleSave() {
  emit('save', props.defaultPath)
}

async function handleSaveAs() {
  const path = await window.electronAPI.saveFileDialog(props.defaultPath)
  if (path) {
    emit('save', path)
  }
}
</script>

<template>
  <div class="save-controls">
    <button class="save-btn" @click="handleSave">저장</button>
    <button class="save-as-btn" @click="handleSaveAs">다른 이름으로 저장</button>
  </div>
</template>

<style scoped>
.save-controls {
  display: flex;
  gap: 8px;
}

.save-btn,
.save-as-btn {
  padding: 8px 20px;
  font-size: 14px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.save-btn {
  background-color: #4a90d9;
  color: #ffffff;
}

.save-btn:hover {
  background-color: #3a7bc8;
}

.save-as-btn {
  background-color: #e0e0e0;
  color: #333;
}

.save-as-btn:hover {
  background-color: #d0d0d0;
}
</style>
