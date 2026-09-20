<script setup lang="ts">
import type { Collage } from '../types'

defineProps<{
  collages: Collage[]
  selectedCollage: string
  selectedCard: string | null
  dirty: boolean
  saving: boolean
  creating: boolean
}>()

const emit = defineEmits<{
  selectCollage: [name: string]
  createCollage: []
  create: []
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
    <button :disabled="!selectedCollage || creating" @click="emit('create')">New card</button>
    <button class="danger" :disabled="!selectedCard || saving" @click="emit('delete')">Delete</button>
    <span v-if="selectedCard" class="current-card">
      {{ selectedCard }}.html<span v-if="dirty || saving" class="dirty" :title="saving ? 'Saving' : 'Unsaved changes'"> ●</span>
    </span>
  </header>
</template>
