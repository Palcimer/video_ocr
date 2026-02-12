<script setup lang="ts">
const emit = defineEmits<{
  fileSelected: [path: string]
}>()

async function handleClick() {
  const path = await window.electronAPI.openVideoDialog()
  if (path) {
    emit('fileSelected', path)
  }
}
</script>

<template>
  <button class="file-loader-btn" @click="handleClick">
    영상 파일 열기
  </button>
</template>

<style scoped>
.file-loader-btn {
  padding: 12px 24px;
  font-size: 16px;
  background-color: #4a90d9;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.file-loader-btn:hover {
  background-color: #3a7bc8;
}
</style>
