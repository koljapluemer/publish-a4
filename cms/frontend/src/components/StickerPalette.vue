<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import type { Sticker } from '../types'

const props = defineProps<{
  stickers: Sticker[]
  busy: boolean
  revision: number
}>()

const emit = defineEmits<{
  insert: [name: string]
  create: [value: { name: string; image: File; width: number; height: number }]
  update: [name: string, value: { image?: File; width: number; height: number }]
  delete: [name: string]
  close: []
}>()

const name = ref('')
const width = ref(25)
const height = ref(25)
const image = ref<File | null>(null)
const edits = reactive<Record<string, { width: number; height: number; image?: File }>>({})

watch(() => props.stickers, stickers => {
  for (const sticker of stickers) {
    const edit = edits[sticker.name]
    if (!edit || !edit.image) {
      edits[sticker.name] = { width: sticker.width, height: sticker.height }
    }
  }
}, { immediate: true })

function chooseNew(event: Event) {
  image.value = (event.target as HTMLInputElement).files?.[0] ?? null
}

function chooseReplacement(name: string, event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) edits[name].image = file
}

function create() {
  if (!name.value || !image.value || width.value <= 0 || height.value <= 0) return
  emit('create', {
    name: name.value,
    image: image.value,
    width: width.value,
    height: height.value,
  })
}
</script>

<template>
  <section class="sticker-palette" aria-label="Stickers">
    <header>
      <strong>Stickers</strong>
      <button aria-label="Close stickers" @click="emit('close')">×</button>
    </header>

    <div v-if="stickers.length" class="sticker-list">
      <article v-for="sticker in stickers" :key="sticker.name" class="sticker-row">
        <button
          class="sticker-preview"
          :title="`Insert ${sticker.name}`"
          :disabled="busy"
          @click="emit('insert', sticker.name)"
        >
          <img
            :src="`/api/stickers/${encodeURIComponent(sticker.name)}/image?r=${revision}`"
            :alt="sticker.name"
          >
          <span>{{ sticker.name }}</span>
        </button>
        <div class="sticker-fields">
          <label>W <input v-model.number="edits[sticker.name].width" type="number" min="0.1" step="0.1"></label>
          <label>H <input v-model.number="edits[sticker.name].height" type="number" min="0.1" step="0.1"></label>
          <span>mm</span>
        </div>
        <div class="sticker-actions">
          <label class="file-button">Replace<input type="file" accept="image/png,image/jpeg,image/gif,image/webp" @change="chooseReplacement(sticker.name, $event)"></label>
          <button :disabled="busy" @click="emit('update', sticker.name, edits[sticker.name])">Save</button>
          <button class="danger" :disabled="busy" @click="emit('delete', sticker.name)">Delete</button>
        </div>
      </article>
    </div>
    <p v-else class="sticker-empty">No stickers yet.</p>

    <form class="sticker-create" @submit.prevent="create">
      <strong>Add sticker</strong>
      <input v-model.trim="name" required pattern="[A-Za-z0-9_-]+" placeholder="Name" aria-label="Sticker name">
      <input required type="file" accept="image/png,image/jpeg,image/gif,image/webp" aria-label="Sticker image" @change="chooseNew">
      <div class="sticker-fields">
        <label>W <input v-model.number="width" required type="number" min="0.1" step="0.1"></label>
        <label>H <input v-model.number="height" required type="number" min="0.1" step="0.1"></label>
        <span>mm</span>
      </div>
      <button type="submit" :disabled="busy || !image">Add</button>
    </form>
  </section>
</template>
