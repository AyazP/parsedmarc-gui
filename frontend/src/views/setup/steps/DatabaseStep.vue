<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useSetupStore } from '@/stores/setup'
import { useToast } from '@/composables/useToast'
import { settingsApi } from '@/api/settings'
import type { DatabaseType } from '@/types/setup'
import AppInput from '@/components/ui/AppInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppAlert from '@/components/ui/AppAlert.vue'

const setupStore = useSetupStore()
const toast = useToast()

const dbType = ref<DatabaseType>(setupStore.wizardData.db_type || 'sqlite')
const dbPath = ref(setupStore.wizardData.db_path || './data/parsedmarc.db')
const dbHost = ref(setupStore.wizardData.db_host || 'localhost')
const dbPort = ref(String(setupStore.wizardData.db_port || 5432))
const dbName = ref(setupStore.wizardData.db_name || 'parsedmarc')
const dbUser = ref(setupStore.wizardData.db_user || '')
const dbPassword = ref(setupStore.wizardData.db_password || '')

const testing = ref(false)
const testPassed = ref(false)
const testMessage = ref('')

const dbTypeOptions: { value: DatabaseType; label: string; desc: string }[] = [
  { value: 'sqlite', label: 'SQLite', desc: 'File-based database, no setup required. Best for small deployments.' },
  { value: 'postgresql', label: 'PostgreSQL', desc: 'Production-grade database. Recommended for enterprise use.' },
  { value: 'mysql', label: 'MySQL', desc: 'Popular relational database. Good for existing MySQL infrastructure.' },
]

const canTest = computed(() => dbHost.value && dbName.value && dbUser.value)

// Reset test status when connection fields change
watch([dbHost, dbPort, dbName, dbUser, dbPassword], () => {
  testPassed.value = false
  testMessage.value = ''
})

// Update default port when DB type changes
watch(dbType, (newType) => {
  if (newType === 'postgresql') {
    dbPort.value = '5432'
  } else if (newType === 'mysql') {
    dbPort.value = '3306'
  }
  testPassed.value = false
  testMessage.value = ''
})

// Sync to store
watch([dbType, dbPath, dbHost, dbPort, dbName, dbUser, dbPassword], () => {
  setupStore.updateWizardData({
    db_type: dbType.value,
    db_path: dbPath.value,
    db_host: dbHost.value,
    db_port: parseInt(dbPort.value) || (dbType.value === 'postgresql' ? 5432 : 3306),
    db_name: dbName.value,
    db_user: dbUser.value,
    db_password: dbPassword.value,
  })
})

async function handleTestConnection() {
  testing.value = true
  testMessage.value = ''
  testPassed.value = false
  try {
    const result = await settingsApi.testDatabaseConnection({
      db_type: dbType.value as 'postgresql' | 'mysql',
      host: dbHost.value,
      port: parseInt(dbPort.value) || 5432,
      database: dbName.value,
      username: dbUser.value,
      password: dbPassword.value,
    })
    testPassed.value = result.success
    testMessage.value = result.message
    if (result.success) {
      toast.success('Connection successful!')
    } else {
      toast.error(result.message)
    }
  } catch (e: unknown) {
    const err = e as { detail?: string; message?: string }
    testMessage.value = err.detail || err.message || 'Connection test failed.'
    toast.error(testMessage.value)
  } finally {
    testing.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">Database Configuration</h2>
      <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
        Choose your database engine. SQLite works well for small deployments; PostgreSQL or MySQL are recommended for production.
      </p>
    </div>

    <!-- Database type radio cards -->
    <div class="space-y-3">
      <div
        v-for="opt in dbTypeOptions"
        :key="opt.value"
        class="relative flex items-start p-4 border rounded-lg cursor-pointer transition-colors"
        :class="dbType === opt.value ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30' : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'"
        @click="dbType = opt.value"
      >
        <input type="radio" :checked="dbType === opt.value" class="mt-0.5 h-4 w-4 text-primary-600" />
        <div class="ml-3">
          <p class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ opt.label }}</p>
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ opt.desc }}</p>
        </div>
      </div>
    </div>

    <!-- SQLite options -->
    <div v-if="dbType === 'sqlite'" class="space-y-4 pt-2">
      <AppInput
        v-model="dbPath"
        label="Database Path"
        placeholder="./data/parsedmarc.db"
        help-text="Path to the SQLite database file. Will be created if it does not exist."
      />
    </div>

    <!-- PostgreSQL / MySQL options -->
    <div v-if="dbType !== 'sqlite'" class="space-y-4 pt-2">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <AppInput
          v-model="dbHost"
          label="Host"
          placeholder="localhost"
        />
        <AppInput
          v-model="dbPort"
          label="Port"
          type="number"
          :placeholder="dbType === 'postgresql' ? '5432' : '3306'"
        />
        <AppInput
          v-model="dbName"
          label="Database Name"
          placeholder="parsedmarc"
        />
        <AppInput
          v-model="dbUser"
          label="Username"
          placeholder="db_user"
        />
        <AppInput
          v-model="dbPassword"
          label="Password"
          type="password"
          placeholder=""
        />
      </div>

      <!-- Test result -->
      <AppAlert
        v-if="testMessage"
        :type="testPassed ? 'success' : 'error'"
        :message="testMessage"
      />

      <AppButton
        size="sm"
        variant="secondary"
        :loading="testing"
        :disabled="!canTest"
        @click="handleTestConnection"
      >
        Test Connection
      </AppButton>
    </div>
  </div>
</template>
