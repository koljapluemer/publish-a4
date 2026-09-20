<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { PreviewMessage } from '../types'

const props = defineProps<{
  collage: string
  revision: number
}>()

const emit = defineEmits<{
  selectCard: [card: string]
  cardMoved: [card: string, top: number, left: number]
  error: [message: string]
}>()

const frame = ref<HTMLIFrameElement | null>(null)
const source = computed(() => props.collage
  ? `/preview/${encodeURIComponent(props.collage)}/?revision=${props.revision}`
  : '')

function receive(event: MessageEvent<PreviewMessage>) {
  if (event.origin !== window.location.origin || event.source !== frame.value?.contentWindow) return
  if (!event.data || event.data.source !== 'a4-preview') return

  if (event.data.type === 'card-selected' && event.data.card) {
    emit('selectCard', event.data.card)
  } else if (
    event.data.type === 'card-moved'
    && event.data.card
    && typeof event.data.top === 'number'
    && typeof event.data.left === 'number'
  ) {
    emit('cardMoved', event.data.card, event.data.top, event.data.left)
  } else if (event.data.type === 'save-error') {
    emit('error', event.data.message || 'Could not save the card position.')
  }
}

onMounted(() => window.addEventListener('message', receive))
onBeforeUnmount(() => window.removeEventListener('message', receive))
</script>

<template>
  <section class="preview-panel">
    <iframe v-if="collage" ref="frame" :src="source" :title="`Preview of ${collage}`" />
    <div v-else class="empty-state">No collages found.</div>
  </section>
</template>
