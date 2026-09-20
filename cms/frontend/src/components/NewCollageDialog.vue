<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

const props = defineProps<{
  open: boolean
  error: string | null
  busy: boolean
}>()

const emit = defineEmits<{
  close: []
  create: [name: string]
}>()

const dialog = ref<HTMLDialogElement | null>(null)
const name = ref('')

watch(() => props.open, async open => {
  await nextTick()
  if (open && !dialog.value?.open) {
    name.value = ''
    dialog.value?.showModal()
  } else if (!open && dialog.value?.open) {
    dialog.value.close()
  }
})
</script>

<template>
  <dialog ref="dialog" @cancel.prevent="emit('close')" @close="emit('close')">
    <form class="dialog-form" @submit.prevent="emit('create', name)">
      <h2>New collage</h2>
      <label>
        Name
        <input v-model.trim="name" required pattern="[A-Za-z0-9_-]+" autofocus>
      </label>
      <p v-if="error" class="dialog-error">{{ error }}</p>
      <footer>
        <button type="button" :disabled="busy" @click="emit('close')">Cancel</button>
        <button class="primary" type="submit" :disabled="busy">{{ busy ? 'Creating…' : 'Create' }}</button>
      </footer>
    </form>
  </dialog>
</template>
