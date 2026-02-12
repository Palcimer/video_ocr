<script setup lang="ts">
defineProps<{
  imageUrl: string
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="popup-overlay"
      @click="emit('close')"
      @keydown="handleKeydown"
      tabindex="0"
    >
      <div class="popup-content" @click.stop>
        <img :src="imageUrl" alt="말풍선 크롭" class="crop-image" />
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.popup-content {
  background: #ffffff;
  padding: 16px;
  border-radius: 8px;
  max-width: 90%;
  max-height: 90%;
  overflow: auto;
}

.crop-image {
  display: block;
  max-width: 100%;
  height: auto;
}
</style>
