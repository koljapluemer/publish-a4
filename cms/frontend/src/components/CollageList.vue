<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Collage } from '../types'

const props = defineProps<{
  collages: Collage[]
  selectedCollage: string
  error: string | null
  busy: boolean
  exporting: boolean
  exportStatus: string | null
}>()

const emit = defineEmits<{
  select: [name: string]
  create: [name: string]
  export: []
}>()

const name = ref('')

// A successful create selects the new collage.
watch(() => props.selectedCollage, selected => {
  if (selected === name.value) name.value = ''
})
</script>

<template>
  <nav class="collage-list">
    <form @submit.prevent="emit('create', name)">
      <input
        v-model.trim="name"
        type="text"
        required
        pattern="[A-Za-z0-9_-]+"
        placeholder="New collage"
        :disabled="busy"
      >
    </form>
    <p v-if="error" class="collage-list-error">{{ error }}</p>
    <ul>
      <li v-for="collage in collages" :key="collage.name">
        <button
          type="button"
          :class="{ active: collage.name === selectedCollage }"
          @click="emit('select', collage.name)"
        >
          {{ collage.name }}
        </button>
      </li>
    </ul>
    <button type="button" class="export-button" :disabled="exporting" @click="emit('export')">
      {{ exporting ? 'Exporting…' : 'Export all' }}
    </button>
    <p v-if="exportStatus" class="collage-list-status">{{ exportStatus }}</p>
  </nav>
</template>
