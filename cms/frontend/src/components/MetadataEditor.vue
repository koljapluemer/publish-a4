<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Metadata } from '../types'

const props = defineProps<{
  metadata: Metadata | null
}>()

const emit = defineEmits<{
  save: [value: Metadata]
}>()

const displayTitle = ref('')
const publish = ref(false)

watch(() => props.metadata, value => {
  displayTitle.value = value?.displayTitle ?? ''
  publish.value = value?.publish ?? false
}, { immediate: true })

function save() {
  if (!props.metadata) return
  if (displayTitle.value === props.metadata.displayTitle && publish.value === props.metadata.publish) return
  emit('save', { displayTitle: displayTitle.value, publish: publish.value })
}
</script>

<template>
  <section class="metadata-panel">
    <h2>A4 metadata</h2>
    <label>
      Display title
      <input v-model="displayTitle" type="text" :disabled="!metadata" @change="save">
    </label>
    <label class="checkbox">
      <input v-model="publish" type="checkbox" :disabled="!metadata" @change="save">
      Publish
    </label>
  </section>
</template>
