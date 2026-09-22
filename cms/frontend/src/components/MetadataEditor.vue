<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Metadata } from '../types'

const props = defineProps<{
  collage: string | null
  metadata: Metadata | null
  renaming: boolean
}>()

const emit = defineEmits<{
  save: [value: Metadata]
  rename: [name: string]
}>()

const name = ref('')
const displayTitle = ref('')
const publish = ref(false)
const tags = ref<string[]>([])
const tagInput = ref('')

watch(() => props.collage, value => {
  name.value = value ?? ''
}, { immediate: true })

watch(() => props.metadata, value => {
  displayTitle.value = value?.displayTitle ?? ''
  publish.value = value?.publish ?? false
  tags.value = value?.tags ?? []
}, { immediate: true })

function tagsEqual(a: string[], b: string[]) {
  return a.length === b.length && a.every((value, index) => value === b[index])
}

function save() {
  if (!props.metadata) return
  if (
    displayTitle.value === props.metadata.displayTitle
    && publish.value === props.metadata.publish
    && tagsEqual(tags.value, props.metadata.tags)
  ) return
  emit('save', { displayTitle: displayTitle.value, publish: publish.value, tags: tags.value })
}

function addTag() {
  const value = tagInput.value.trim()
  tagInput.value = ''
  if (!value || tags.value.includes(value)) return
  tags.value = [...tags.value, value]
  save()
}

function removeTag(tag: string) {
  tags.value = tags.value.filter(item => item !== tag)
  save()
}

function rename() {
  if (!props.collage || props.renaming) return
  const trimmed = name.value.trim()
  if (!trimmed || trimmed === props.collage) {
    name.value = props.collage
    return
  }
  emit('rename', trimmed)
}
</script>

<template>
  <section class="metadata-panel">
    <h2>A4 metadata</h2>
    <form class="rename-form" @submit.prevent="rename">
      <label>
        Collage name
        <input
          v-model.trim="name"
          type="text"
          required
          pattern="[A-Za-z0-9_-]+"
          :disabled="!collage || renaming"
        >
      </label>
      <button type="submit" :disabled="!collage || renaming || name === collage">
        {{ renaming ? 'Renaming…' : 'Rename' }}
      </button>
    </form>
    <label>
      Display title
      <input v-model="displayTitle" type="text" :disabled="!metadata" @change="save">
    </label>
    <label class="checkbox">
      <input v-model="publish" type="checkbox" :disabled="!metadata" @change="save">
      Publish
    </label>
    <label>
      Tags
      <div class="tag-input">
        <input
          v-model.trim="tagInput"
          type="text"
          :disabled="!metadata"
          placeholder="Add a tag"
          @keydown.enter.prevent="addTag"
        >
        <button type="button" :disabled="!metadata || !tagInput.trim()" @click="addTag">Add</button>
      </div>
      <ul v-if="tags.length" class="tag-list">
        <li v-for="tag in tags" :key="tag" class="tag">
          {{ tag }}
          <button type="button" aria-label="Remove tag" @click="removeTag(tag)">×</button>
        </li>
      </ul>
    </label>
  </section>
</template>
