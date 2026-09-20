<script setup lang="ts">
import type { Collage } from '../types'

defineProps<{
  collages: Collage[]
  selectedCollage: string
  selectedCard: string | null
  dirty: boolean
  saving: boolean
}>()

const emit = defineEmits<{
  selectCollage: [name: string]
  createCollage: []
  create: []
  save: []
  delete: []
}>()
</script>

<template>
  <header class="toolbar">
    <label class="field-inline">
      <span>Collage</span>
      <select :value="selectedCollage" @change="emit('selectCollage', ($event.target as HTMLSelectElement).value)">
        <option v-if="!collages.length" value="">No collages</option>
        <option v-for="collage in collages" :key="collage.name" :value="collage.name">
          {{ collage.name }}
        </option>
      </select>
    </label>
    <button @click="emit('createCollage')">New collage</button>
    <span class="separator" />
    <button :disabled="!selectedCollage" @click="emit('create')">New card</button>
    <button class="primary" :disabled="!selectedCard || !dirty || saving" @click="emit('save')">
      {{ saving ? 'Saving…' : 'Save' }}
    </button>
    <button class="danger" :disabled="!selectedCard || saving" @click="emit('delete')">Delete</button>
    <span v-if="selectedCard" class="current-card">
      {{ selectedCard }}.html<span v-if="dirty" class="dirty" title="Unsaved changes"> ●</span>
    </span>
  </header>
</template>
