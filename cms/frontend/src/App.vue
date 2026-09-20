<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import * as api from './api'
import type { Card, Collage } from './types'
import CardEditor from './components/CardEditor.vue'
import CollagePreview from './components/CollagePreview.vue'
import NewCollageDialog from './components/NewCollageDialog.vue'
import NewCardDialog from './components/NewCardDialog.vue'
import Toolbar from './components/Toolbar.vue'

const collages = ref<Collage[]>([])
const selectedCollage = ref('')
const selectedCard = ref<Card | null>(null)
const source = ref('')
const savedSource = ref('')
const saving = ref(false)
const revision = ref(0)
const error = ref<string | null>(null)
const createOpen = ref(false)
const createError = ref<string | null>(null)
const creating = ref(false)
const createCollageOpen = ref(false)
const createCollageError = ref<string | null>(null)
const creatingCollage = ref(false)

const dirty = computed(() => selectedCard.value !== null && source.value !== savedSource.value)

function report(value: unknown) {
  error.value = value instanceof Error ? value.message : String(value)
}

function mayDiscard(): boolean {
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
  if (name === selectedCollage.value || !mayDiscard()) return
  selectedCollage.value = name
  clearCard()
  error.value = null
}

async function chooseCard(name: string) {
  if (!selectedCollage.value || selectedCard.value?.name === name || !mayDiscard()) return
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

async function save() {
  if (!selectedCollage.value || !selectedCard.value || !dirty.value || saving.value) return
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

async function create(value: { name: string; source: string; top: number; left: number }) {
  if (!selectedCollage.value || creating.value) return
  creating.value = true
  createError.value = null
  try {
    const card = await api.createCard(selectedCollage.value, value)
    await refreshCollages()
    selectedCard.value = card
    source.value = card.source
    savedSource.value = card.source
    createOpen.value = false
    revision.value += 1
  } catch (reason) {
    createError.value = reason instanceof Error ? reason.message : String(reason)
  } finally {
    creating.value = false
  }
}

function openCreateCollage() {
  if (!mayDiscard()) return
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
  const collage = collages.value.find(item => item.name === selectedCollage.value)
  const card = collage?.cards.find(item => item.name === name)
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
      @select-collage="chooseCollage"
      @create-collage="openCreateCollage"
      @create="createOpen = true"
      @save="save"
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
        v-model="source"
        :disabled="!selectedCard"
        @save="save"
      />
    </div>
    <NewCardDialog
      :open="createOpen"
      :error="createError"
      :busy="creating"
      @close="createOpen = false"
      @create="create"
    />
    <NewCollageDialog
      :open="createCollageOpen"
      :error="createCollageError"
      :busy="creatingCollage"
      @close="createCollageOpen = false"
      @create="createCollage"
    />
  </main>
</template>
