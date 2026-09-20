<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

const props = defineProps<{
  open: boolean
  error: string | null
  busy: boolean
}>()

const emit = defineEmits<{
  close: []
  create: [value: { name: string; source: string; top: number; left: number }]
}>()

const dialog = ref<HTMLDialogElement | null>(null)
const name = ref('')
const top = ref(10)
const left = ref(10)
const source = ref('<article>New card</article>\n')

watch(() => props.open, async open => {
  await nextTick()
  if (open && !dialog.value?.open) {
    name.value = ''
    top.value = 10
    left.value = 10
    source.value = '<article>New card</article>\n'
    dialog.value?.showModal()
  } else if (!open && dialog.value?.open) {
    dialog.value.close()
  }
})

function submit() {
  emit('create', { name: name.value, source: source.value, top: top.value, left: left.value })
}
</script>

<template>
  <dialog ref="dialog" @cancel.prevent="emit('close')" @close="emit('close')">
    <form class="dialog-form" @submit.prevent="submit">
      <h2>New card</h2>
      <label>
        Name
        <input v-model.trim="name" required pattern="[A-Za-z0-9_-]+" autofocus>
      </label>
      <div class="position-fields">
        <label>Top (mm)<input v-model.number="top" type="number" required></label>
        <label>Left (mm)<input v-model.number="left" type="number" required></label>
      </div>
      <label>
        Initial HTML
        <textarea v-model="source" rows="6" required />
      </label>
      <p v-if="error" class="dialog-error">{{ error }}</p>
      <footer>
        <button type="button" :disabled="busy" @click="emit('close')">Cancel</button>
        <button class="primary" type="submit" :disabled="busy">{{ busy ? 'Creating…' : 'Create' }}</button>
      </footer>
    </form>
  </dialog>
</template>
