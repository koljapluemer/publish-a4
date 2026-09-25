<script setup lang="ts">
import { reactive, watch } from 'vue'
import type { Collage } from '../types'

const props = defineProps<{
  collages: Collage[]
  revision: number
}>()

const emit = defineEmits<{
  select: [name: string]
}>()

// Collages without an exported thumbnail fall back to their name.
const missing = reactive(new Set<string>())
watch(() => props.revision, () => missing.clear())
</script>

<template>
  <section class="dashboard">
    <div v-if="collages.length" class="dashboard-grid">
      <button
        v-for="collage in collages"
        :key="collage.name"
        type="button"
        class="dashboard-card"
        :title="collage.name"
        @click="emit('select', collage.name)"
      >
        <img
          v-if="!missing.has(collage.name)"
          :src="`/thumbnails/${encodeURIComponent(collage.name)}?revision=${revision}`"
          :alt="collage.name"
          loading="lazy"
          @error="missing.add(collage.name)"
        >
        <span v-else class="dashboard-card-missing">{{ collage.name }}</span>
      </button>
    </div>
    <div v-else class="empty-state">No collages found.</div>
  </section>
</template>
