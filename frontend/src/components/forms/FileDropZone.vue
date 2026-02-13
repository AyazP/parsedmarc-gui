<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  accept?: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  'file-selected': [file: File]
}>()

const dragging = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)

function handleDrop(e: DragEvent) {
  dragging.value = false
  const file = e.dataTransfer?.files[0]
  if (file) emit('file-selected', file)
}

function handleFileInput(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) emit('file-selected', file)
  input.value = ''
}

function openFilePicker() {
  inputRef.value?.click()
}
</script>

<template>
  <div
    class="border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer"
    :class="[
      dragging ? 'border-primary-400 bg-primary-50' : 'border-gray-300 hover:border-gray-400',
      disabled ? 'opacity-50 cursor-not-allowed' : '',
    ]"
    @click="!disabled && openFilePicker()"
    @dragover.prevent="dragging = true"
    @dragleave.prevent="dragging = false"
    @drop.prevent="handleDrop"
  >
    <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
    </svg>
    <p class="mt-2 text-sm text-gray-600">
      <span class="font-semibold text-primary-600">Click to upload</span> or drag and drop
    </p>
    <p class="mt-1 text-xs text-gray-500">
      <slot name="hint">XML, GZ, ZIP, EML, or MSG files</slot>
    </p>
    <input
      ref="inputRef"
      type="file"
      class="hidden"
      :accept="accept"
      :disabled="disabled"
      @change="handleFileInput"
    />
  </div>
</template>
