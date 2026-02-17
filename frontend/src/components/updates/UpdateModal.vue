<script setup lang="ts">
import { computed } from 'vue'
import { useUpdateStore } from '@/stores/updates'
import AppModal from '@/components/ui/AppModal.vue'
import AppButton from '@/components/ui/AppButton.vue'

defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const updateStore = useUpdateStore()

const dockerInstructions = `1. Pull the latest image:
   docker compose pull gui

2. Restart the container:
   docker compose up -d gui

3. Verify the update:
   docker compose logs gui`

const gitInstructions = `1. Pull the latest changes:
   git pull origin master

2. Install updated dependencies:
   cd backend && pip install -r requirements.txt
   cd ../frontend && npm ci && npm run build

3. Restart the application`

const instructions = computed(() =>
  updateStore.status?.is_docker ? dockerInstructions : gitInstructions
)

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

function handleDismiss() {
  updateStore.dismiss()
  emit('close')
}
</script>

<template>
  <AppModal :open="open" title="Update Available" @close="$emit('close')">
    <div class="space-y-4" v-if="updateStore.status">
      <!-- Version comparison -->
      <div class="flex items-center gap-3">
        <span class="text-sm text-gray-500 dark:text-gray-400">
          {{ updateStore.status.current_version }}
        </span>
        <svg class="w-4 h-4 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
        <span class="text-sm font-semibold text-green-700">
          {{ updateStore.status.latest_version }}
        </span>
      </div>

      <!-- Published date -->
      <p class="text-xs text-gray-500 dark:text-gray-400">
        Released: {{ formatDate(updateStore.status.published_at) }}
      </p>

      <!-- Release notes -->
      <div v-if="updateStore.status.release_notes" class="space-y-1">
        <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100">Release Notes</h4>
        <div class="rounded-lg bg-gray-50 dark:bg-gray-900 p-3 text-sm text-gray-700 dark:text-gray-300 max-h-48 overflow-auto whitespace-pre-wrap">
          {{ updateStore.status.release_notes }}
        </div>
      </div>

      <!-- Update instructions -->
      <div class="space-y-1">
        <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100">
          Update Instructions
          <span class="text-xs font-normal text-gray-500 dark:text-gray-400 ml-1">
            ({{ updateStore.status.is_docker ? 'Docker' : 'Git' }})
          </span>
        </h4>
        <pre class="rounded-lg bg-gray-900 text-green-400 p-3 text-xs overflow-auto max-h-40 font-mono">{{ instructions }}</pre>
      </div>

      <!-- Link to release page -->
      <a
        :href="updateStore.status.release_url"
        target="_blank"
        rel="noopener noreferrer"
        class="inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
      >
        View on GitHub
        <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
          <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
          <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
        </svg>
      </a>
    </div>

    <template #footer>
      <div class="flex justify-end gap-3">
        <AppButton variant="secondary" size="sm" @click="handleDismiss">
          Dismiss
        </AppButton>
        <AppButton size="sm" @click="$emit('close')">
          Close
        </AppButton>
      </div>
    </template>
  </AppModal>
</template>
