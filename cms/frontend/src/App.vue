<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as api from './api'
import type { Card, Collage, Metadata } from './types'
import CanvasTools from './components/CanvasTools.vue'
import CardEditor from './components/CardEditor.vue'
import CollageDashboard from './components/CollageDashboard.vue'
import CollageList from './components/CollageList.vue'
import CollagePreview from './components/CollagePreview.vue'
import MetadataEditor from './components/MetadataEditor.vue'

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
const createCollageError = ref<string | null>(null)
const creatingCollage = ref(false)
const renamingCollage = ref(false)
const exporting = ref(false)
const exportStatus = ref<string | null>(null)
const exportRevision = ref(0)

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

function pastelColor(): string {
  const hue = Math.floor(Math.random() * 360)
  return `hsl(${hue} 100% 87.5%)`
}

async function create() {
  if (!selectedCollage.value || creating.value || !await mayDiscard()) return
  creating.value = true
  error.value = null
  try {
    const offset = 10 + (currentCards().length % 10) * 5
    const color = pastelColor()
    const card = await api.createCard(selectedCollage.value, {
      name: newCardName(),
      source: `<article class='p' style='background: ${color}'>  </article>\n`,
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

async function createCollage(name: string) {
  if (creatingCollage.value || !await mayDiscard()) return
  creatingCollage.value = true
  createCollageError.value = null
  try {
    const collage = await api.createCollage(name)
    await refreshCollages()
    selectedCollage.value = collage.name
    clearCard()
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

async function saveMetadata(value: Metadata) {
  const collage = collages.value.find(item => item.name === selectedCollage.value)
  if (!collage) return
  try {
    error.value = null
    collage.metadata = await api.updateMetadata(collage.name, value)
  } catch (reason) {
    report(reason)
    await refreshCollages()
  }
}

async function renameCollage(name: string) {
  if (!selectedCollage.value || renamingCollage.value) return
  renamingCollage.value = true
  error.value = null
  try {
    const result = await api.renameCollage(selectedCollage.value, name)
    await refreshCollages()
    selectedCollage.value = result.name
    revision.value += 1
  } catch (reason) {
    report(reason)
  } finally {
    renamingCollage.value = false
  }
}

let exportQueued = false

// Requests arriving during an export queue one more run, so later edits are picked up.
async function exportAll() {
  if (exporting.value) {
    exportQueued = true
    return
  }
  await save()
  exporting.value = true
  exportStatus.value = null
  try {
    const { total, rendered } = await api.exportAll()
    exportStatus.value = `Rendered ${rendered} of ${total} collages`
    if (rendered) exportRevision.value += 1
  } catch (reason) {
    report(reason)
  } finally {
    exporting.value = false
  }
  if (exportQueued) {
    exportQueued = false
    await exportAll()
  }
}

// Export in the background whenever the dashboard is shown, including on startup.
watch(selectedCollage, name => {
  if (!name) void exportAll()
}, { immediate: true })

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
  <main class="app-shell" :class="{ 'dashboard-mode': !selectedCollage }">
    <CollageList
      :collages="collages"
      :selected-collage="selectedCollage"
      :error="createCollageError"
      :busy="creatingCollage"
      @select="chooseCollage"
      :exporting="exporting"
      :export-status="exportStatus"
      @create="createCollage"
      @export="exportAll"
    />
    <div class="canvas">
      <CollageDashboard v-if="!selectedCollage" :collages="collages" :revision="exportRevision" @select="chooseCollage" />
      <CollagePreview
        v-else
        :collage="selectedCollage"
        :revision="revision"
        @select-card="chooseCard"
        @card-moved="cardMoved"
        @error="report"
      />
      <div v-if="error" class="error-bar">
        <span>{{ error }}</span>
        <button aria-label="Dismiss error" @click="error = null">×</button>
      </div>
      <CanvasTools
        v-if="selectedCollage"
        :has-collage="!!selectedCollage"
        :has-card="!!selectedCard"
        :saving="saving"
        :creating="creating"
        @create="create"
        @create-image="createImage"
        @delete="remove"
      />
    </div>
    <div v-if="selectedCollage" class="sidebar">
      <div v-if="selectedCard" class="current-card">
        {{ selectedCard.name }}.html<span v-if="dirty || saving" class="dirty" :title="saving ? 'Saving' : 'Unsaved changes'"> ●</span>
      </div>
      <CardEditor
        ref="editor"
        v-model="source"
        :disabled="!selectedCard"
        @save="save"
        @blur="save"
      />
      <MetadataEditor
        :collage="selectedCollage || null"
        :metadata="collages.find(item => item.name === selectedCollage)?.metadata ?? null"
        :renaming="renamingCollage"
        @save="saveMetadata"
        @rename="renameCollage"
      />
    </div>
  </main>
</template>
