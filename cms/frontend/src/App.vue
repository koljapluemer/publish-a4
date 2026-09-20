<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as api from './api'
import type { Card, Collage } from './types'
import CardEditor from './components/CardEditor.vue'
import CollagePreview from './components/CollagePreview.vue'
import NewCollageDialog from './components/NewCollageDialog.vue'
import Toolbar from './components/Toolbar.vue'

const collages = ref<Collage[]>([])
const selectedCollage = ref('')
const selectedCard = ref<Card | null>(null)
const source = ref('')
const savedSource = ref('')
const saving = ref(false)
const revision = ref(0)
const error = ref<string | null>(null)
const creating = ref(false)
const editor = ref<InstanceType<typeof CardEditor> | null>(null)
const createCollageOpen = ref(false)
const createCollageError = ref<string | null>(null)
const creatingCollage = ref(false)

const dirty = computed(() => selectedCard.value !== null && source.value !== savedSource.value)

function report(value: unknown) {
  error.value = value instanceof Error ? value.message : String(value)
}

async function mayDiscard(): Promise<boolean> {
  await save()
  return !dirty.value || window.confirm('Discard unsaved changes?')
}

function clearCard() {
  selectedCard.value = null
  source.value = ''
  savedSource.value = ''
}

async function refreshCollages() {
  collages.value = await api.listCollages()
}

async function initialize() {
  try {
    await refreshCollages()
    selectedCollage.value = collages.value[0]?.name || ''
  } catch (value) {
    report(value)
  }
}

async function chooseCollage(name: string) {
  if (name === selectedCollage.value || !await mayDiscard()) return
  selectedCollage.value = name
  clearCard()
  error.value = null
}

async function chooseCard(name: string) {
  if (!selectedCollage.value || selectedCard.value?.name === name || !await mayDiscard()) return
  try {
    error.value = null
    const card = await api.getCard(selectedCollage.value, name)
    selectedCard.value = card
    source.value = card.source
    savedSource.value = card.source
  } catch (value) {
    report(value)
  }
}

let pendingSave: Promise<void> | null = null

function save(): Promise<void> {
  pendingSave ??= persist().finally(() => { pendingSave = null })
  return pendingSave
}

async function persist() {
  if (!selectedCollage.value || !selectedCard.value || !dirty.value) return
  saving.value = true
  error.value = null
  try {
    const card = await api.updateCard(selectedCollage.value, selectedCard.value.name, source.value)
    selectedCard.value = card
    savedSource.value = card.source
    revision.value += 1
  } catch (value) {
    report(value)
  } finally {
    saving.value = false
  }
}

function newCardName(): string {
  const taken = new Set(currentCards().map(card => card.name))
  let number = 1
  while (taken.has(`card-${number}`)) number += 1
  return `card-${number}`
}

function currentCards() {
  return collages.value.find(item => item.name === selectedCollage.value)?.cards ?? []
}

async function create() {
  if (!selectedCollage.value || creating.value || !await mayDiscard()) return
  creating.value = true
  error.value = null
  try {
    const offset = 10 + (currentCards().length % 10) * 5
    const card = await api.createCard(selectedCollage.value, {
      name: newCardName(),
      source: '<article>New card</article>\n',
      top: offset,
      left: offset,
    })
    await refreshCollages()
    selectedCard.value = card
    source.value = card.source
    savedSource.value = card.source
    revision.value += 1
    await nextTick()
    editor.value?.focus()
  } catch (reason) {
    report(reason)
  } finally {
    creating.value = false
  }
}

async function createImage() {
  if (!selectedCollage.value || creating.value || !await mayDiscard()) return
  creating.value = true
  error.value = null
  try {
    if (!navigator.clipboard?.read) {
      throw new Error('Reading images from the clipboard is not supported by this browser.')
    }
    const items = await navigator.clipboard.read()
    const item = items.find(value => value.types.some(type => type.startsWith('image/')))
    const imageType = item?.types.find(type => type.startsWith('image/'))
    if (!item || !imageType) throw new Error('The clipboard does not contain an image.')

    const offset = 10 + (currentCards().length % 10) * 5
    const card = await api.createImageCard(selectedCollage.value, {
      name: newCardName(),
      image: await item.getType(imageType),
      top: offset,
      left: offset,
    })
    await refreshCollages()
    selectedCard.value = card
    source.value = card.source
    savedSource.value = card.source
    revision.value += 1
    await nextTick()
    editor.value?.focus()
  } catch (reason) {
    report(reason)
  } finally {
    creating.value = false
  }
}

async function openCreateCollage() {
  if (!await mayDiscard()) return
  createCollageError.value = null
  createCollageOpen.value = true
}

async function createCollage(name: string) {
  if (creatingCollage.value) return
  creatingCollage.value = true
  createCollageError.value = null
  try {
    const collage = await api.createCollage(name)
    await refreshCollages()
    selectedCollage.value = collage.name
    clearCard()
    createCollageOpen.value = false
    revision.value += 1
  } catch (reason) {
    createCollageError.value = reason instanceof Error ? reason.message : String(reason)
  } finally {
    creatingCollage.value = false
  }
}

async function remove() {
  if (!selectedCollage.value || !selectedCard.value || saving.value) return
  const name = selectedCard.value.name
  if (!window.confirm(`Delete ${name}.html? This cannot be undone.`)) return
  try {
    error.value = null
    await api.deleteCard(selectedCollage.value, name)
    clearCard()
    await refreshCollages()
    revision.value += 1
  } catch (value) {
    report(value)
  }
}

function cardMoved(name: string, top: number, left: number) {
  const card = currentCards().find(item => item.name === name)
  if (card) Object.assign(card, { top, left })
  if (selectedCard.value?.name === name) Object.assign(selectedCard.value, { top, left })
}

function beforeUnload(event: BeforeUnloadEvent) {
  if (!dirty.value) return
  event.preventDefault()
}

onMounted(() => {
  window.addEventListener('beforeunload', beforeUnload)
  void initialize()
})
onBeforeUnmount(() => window.removeEventListener('beforeunload', beforeUnload))
</script>

<template>
  <main class="app-shell">
    <Toolbar
      :collages="collages"
      :selected-collage="selectedCollage"
      :selected-card="selectedCard?.name || null"
      :dirty="dirty"
      :saving="saving"
      :creating="creating"
      @select-collage="chooseCollage"
      @create-collage="openCreateCollage"
      @create="create"
      @create-image="createImage"
      @delete="remove"
    />
    <div v-if="error" class="error-bar">
      <span>{{ error }}</span>
      <button aria-label="Dismiss error" @click="error = null">×</button>
    </div>
    <div class="workspace">
      <CollagePreview
        :collage="selectedCollage"
        :revision="revision"
        @select-card="chooseCard"
        @card-moved="cardMoved"
        @error="report"
      />
      <CardEditor
        ref="editor"
        v-model="source"
        :disabled="!selectedCard"
        @save="save"
        @blur="save"
      />
    </div>
    <NewCollageDialog
      :open="createCollageOpen"
      :error="createCollageError"
      :busy="creatingCollage"
      @close="createCollageOpen = false"
      @create="createCollage"
    />
  </main>
</template>
