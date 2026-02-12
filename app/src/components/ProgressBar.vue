<script setup lang="ts">
import type { OcrPhase } from '../types'

const props = defineProps<{
  phase: OcrPhase
  current: number
  total: number
}>()

const PHASE_LABELS: Record<OcrPhase, string> = {
  scan: '프레임 스캔 중',
  ocr: 'OCR 실행 중',
}

function percentage(): number {
  if (props.total <= 0) return 0
  return Math.round((props.current / props.total) * 100)
}
</script>

<template>
  <div class="progress-container">
    <p class="progress-label">
      {{ PHASE_LABELS[phase] }} ({{ current }} / {{ total }})
    </p>
    <div class="progress-track">
      <div class="progress-fill" :style="{ width: percentage() + '%' }" />
    </div>
    <p class="progress-percent">{{ percentage() }}%</p>
  </div>
</template>

<style scoped>
.progress-container {
  width: 100%;
  max-width: 500px;
  text-align: center;
}

.progress-label {
  margin-bottom: 8px;
  font-size: 14px;
  color: #333;
}

.progress-track {
  width: 100%;
  height: 20px;
  background-color: #e0e0e0;
  border-radius: 10px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: #4a90d9;
  transition: width 0.2s ease;
}

.progress-percent {
  margin-top: 4px;
  font-size: 13px;
  color: #666;
}
</style>
