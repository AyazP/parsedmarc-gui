<script setup lang="ts">
import { ref, watch } from 'vue'
import { useSetupStore } from '@/stores/setup'
import AppInput from '@/components/ui/AppInput.vue'

const setupStore = useSetupStore()
const dbPath = ref(setupStore.wizardData.db_path || './data/parsedmarc.db')

watch(dbPath, () => {
  setupStore.updateWizardData({ db_path: dbPath.value })
})
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">Database Configuration</h2>
      <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
        Configure where ParseDMARC stores its data. The default SQLite database works well for most deployments.
      </p>
    </div>
    <AppInput
      v-model="dbPath"
      label="Database Path"
      placeholder="./data/parsedmarc.db"
      help-text="Path to the SQLite database file. Will be created if it does not exist."
    />
  </div>
</template>
