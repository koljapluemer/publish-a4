<script setup lang="ts">
import { ImagePlus, Plus, Trash2 } from 'lucide-vue-next'

defineProps<{
  hasCollage: boolean
  hasCard: boolean
  saving: boolean
  creating: boolean
}>()

const emit = defineEmits<{
  create: []
  createImage: []
  delete: []
}>()
</script>

<template>
  <div class="canvas-tools">
    <button title="New card" aria-label="New card" :disabled="!hasCollage || creating" @click="emit('create')">
      <Plus :size="16" />
    </button>
    <button
      title="Image card from clipboard"
      aria-label="Image card from clipboard"
      :disabled="!hasCollage || creating"
      @click="emit('createImage')"
    >
      <ImagePlus :size="16" />
    </button>
    <button
      class="danger"
      title="Delete card"
      aria-label="Delete card"
      :disabled="!hasCard || saving"
      @click="emit('delete')"
    >
      <Trash2 :size="16" />
    </button>
  </div>
</template>
