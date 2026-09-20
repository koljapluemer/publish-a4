<script setup lang="ts">
import { basicSetup } from 'codemirror'
import { html } from '@codemirror/lang-html'
import { Compartment, EditorState } from '@codemirror/state'
import { EditorView, keymap } from '@codemirror/view'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps<{
  modelValue: string
  disabled: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  save: []
}>()

const host = ref<HTMLElement | null>(null)
let editor: EditorView | null = null
const editable = new Compartment()

onMounted(() => {
  editor = new EditorView({
    parent: host.value!,
    state: EditorState.create({
      doc: props.modelValue,
      extensions: [
        basicSetup,
        html(),
        EditorView.lineWrapping,
        editable.of(EditorView.editable.of(!props.disabled)),
        keymap.of([{
          key: 'Mod-s',
          preventDefault: true,
          run: () => {
            emit('save')
            return true
          },
        }]),
        EditorView.updateListener.of(update => {
          if (update.docChanged) emit('update:modelValue', update.state.doc.toString())
        }),
      ],
    }),
  })
})

watch(() => props.modelValue, value => {
  if (!editor || editor.state.doc.toString() === value) return
  editor.dispatch({ changes: { from: 0, to: editor.state.doc.length, insert: value } })
})

watch(() => props.disabled, disabled => {
  editor?.dispatch({ effects: editable.reconfigure(EditorView.editable.of(!disabled)) })
})

onBeforeUnmount(() => editor?.destroy())
</script>

<template>
  <section class="editor-panel">
    <div v-if="disabled" class="editor-empty">Select a card in the preview.</div>
    <div ref="host" class="editor-host" :class="{ hidden: disabled }" />
  </section>
</template>
