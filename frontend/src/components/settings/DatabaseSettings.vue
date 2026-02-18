<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { settingsApi } from '@/api/settings'
import { useToast } from '@/composables/useToast'
import type { DatabaseInfo, DatabaseTestRequest, DatabaseMigrateResponse, DatabasePurgeResponse } from '@/types/settings'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppAlert from '@/components/ui/AppAlert.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppToggle from '@/components/ui/AppToggle.vue'

const toast = useToast()

const loading = ref(true)
const dbInfo = ref<DatabaseInfo | null>(null)

// Migration form state
const showMigrateForm = ref(false)
const testing = ref(false)
const migrating = ref(false)
const testPassed = ref(false)
const testMessage = ref('')

const dbType = ref<'postgresql' | 'mysql'>('postgresql')
const host = ref('localhost')
const port = ref(5432)
const database = ref('parsedmarc')
const username = ref('')
const password = ref('')
const migrateData = ref(true)

const migrateResult = ref<DatabaseMigrateResponse | null>(null)

// Purge state
const showPurgeConfirm = ref(false)
const purging = ref(false)
const purgeResult = ref<DatabasePurgeResponse | null>(null)

const isSqlite = computed(() => dbInfo.value?.db_type === 'sqlite')

// Auto-fill default port when DB type changes
watch(dbType, (newType) => {
  port.value = newType === 'postgresql' ? 5432 : 3306
  // Reset test status when config changes
  testPassed.value = false
  testMessage.value = ''
})

// Reset test status when any connection field changes
watch([host, port, database, username, password], () => {
  testPassed.value = false
  testMessage.value = ''
})

const dbTypeOptions = [
  { value: 'postgresql', label: 'PostgreSQL' },
  { value: 'mysql', label: 'MySQL' },
]

const dbTypeBadgeVariant = computed(() => {
  if (!dbInfo.value) return 'neutral' as const
  const t = dbInfo.value.db_type
  if (t === 'postgresql') return 'info' as const
  if (t === 'mysql') return 'info' as const
  return 'neutral' as const
})

const dbTypeLabel = computed(() => {
  if (!dbInfo.value) return 'Unknown'
  const t = dbInfo.value.db_type
  if (t === 'postgresql') return 'PostgreSQL'
  if (t === 'mysql') return 'MySQL'
  return 'SQLite'
})

const totalRows = computed(() => {
  if (!dbInfo.value?.table_counts) return 0
  return Object.values(dbInfo.value.table_counts).reduce((sum, n) => sum + n, 0)
})

const canTest = computed(() => host.value && database.value && username.value)

onMounted(async () => {
  try {
    dbInfo.value = await settingsApi.getDatabaseInfo()
  } catch {
    toast.error('Failed to load database information.')
  } finally {
    loading.value = false
  }
})

async function handleTestConnection() {
  testing.value = true
  testMessage.value = ''
  testPassed.value = false
  try {
    const config: DatabaseTestRequest = {
      db_type: dbType.value,
      host: host.value,
      port: port.value,
      database: database.value,
      username: username.value,
      password: password.value,
    }
    const result = await settingsApi.testDatabaseConnection(config)
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

async function handleMigrate() {
  migrating.value = true
  migrateResult.value = null
  try {
    const result = await settingsApi.migrateDatabase({
      db_type: dbType.value,
      host: host.value,
      port: port.value,
      database: database.value,
      username: username.value,
      password: password.value,
      migrate_data: migrateData.value,
    })
    migrateResult.value = result
    if (result.success) {
      toast.success('Migration completed! Restart the application to use the new database.')
      // Refresh DB info
      dbInfo.value = await settingsApi.getDatabaseInfo()
    } else {
      toast.error(result.message)
    }
  } catch (e: unknown) {
    const err = e as { detail?: string; message?: string }
    toast.error(err.detail || err.message || 'Migration failed.')
  } finally {
    migrating.value = false
  }
}

async function handlePurge() {
  purging.value = true
  purgeResult.value = null
  try {
    const result = await settingsApi.purgeDatabase()
    purgeResult.value = result
    if (result.success) {
      toast.success('Database purged successfully.')
      dbInfo.value = await settingsApi.getDatabaseInfo()
    } else {
      toast.error(result.message)
    }
  } catch (e: unknown) {
    const err = e as { detail?: string; message?: string }
    toast.error(err.detail || err.message || 'Purge failed.')
  } finally {
    purging.value = false
    showPurgeConfirm.value = false
  }
}

function cancelPurge() {
  showPurgeConfirm.value = false
  purgeResult.value = null
}

function cancelMigrate() {
  showMigrateForm.value = false
  testPassed.value = false
  testMessage.value = ''
  migrateResult.value = null
  // Reset form
  dbType.value = 'postgresql'
  host.value = 'localhost'
  port.value = 5432
  database.value = 'parsedmarc'
  username.value = ''
  password.value = ''
  migrateData.value = true
}
</script>

<template>
  <AppCard>
    <template #header>
      <div class="flex items-center justify-between">
        <h2 class="text-base font-semibold text-gray-900 dark:text-gray-100">Database</h2>
        <div v-if="!showMigrateForm && dbInfo" class="flex items-center gap-2">
          <AppButton
            v-if="isSqlite"
            size="sm"
            variant="danger"
            :disabled="purging || totalRows === 0"
            @click="showPurgeConfirm = true"
          >
            Purge Database
          </AppButton>
          <AppButton
            size="sm"
            variant="secondary"
            @click="showMigrateForm = true"
          >
            Migrate Database
          </AppButton>
        </div>
      </div>
    </template>

    <!-- Current database info -->
    <div v-if="loading" class="text-sm text-gray-500 dark:text-gray-400">Loading...</div>
    <div v-else-if="dbInfo" class="space-y-5">
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Engine</p>
          <div class="mt-1 flex items-center gap-2">
            <p class="text-sm font-semibold text-gray-900 dark:text-gray-100">{{ dbTypeLabel }}</p>
            <AppBadge :text="dbTypeLabel" :variant="dbTypeBadgeVariant" />
          </div>
        </div>
        <div>
          <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Connection</p>
          <p class="mt-1 text-sm font-mono text-gray-700 dark:text-gray-300 break-all">{{ dbInfo.connection_string }}</p>
        </div>
        <div>
          <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Total Records</p>
          <p class="mt-1 text-sm font-semibold text-gray-900 dark:text-gray-100">{{ totalRows.toLocaleString() }}</p>
        </div>
      </div>

      <!-- Table counts -->
      <div v-if="dbInfo.table_counts && Object.keys(dbInfo.table_counts).length > 0">
        <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Table Breakdown</p>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div
            v-for="(count, table) in dbInfo.table_counts"
            :key="table"
            class="bg-gray-50 dark:bg-gray-700/50 rounded-lg px-4 py-3"
          >
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 truncate">{{ table }}</p>
            <p class="mt-1 text-sm font-semibold text-gray-900 dark:text-gray-100">{{ count.toLocaleString() }}</p>
          </div>
        </div>
      </div>

      <!-- Purge confirmation (SQLite only) -->
      <div v-if="isSqlite && !showMigrateForm && (showPurgeConfirm || purgeResult)" class="border-t border-gray-200 dark:border-gray-700 pt-4 space-y-3">
        <div v-if="showPurgeConfirm" class="space-y-3">
          <AppAlert
            type="error"
            message="This will permanently delete ALL data from every table. This action cannot be undone."
          />
          <div class="flex items-center gap-3">
            <AppButton
              size="sm"
              variant="danger"
              :loading="purging"
              @click="handlePurge"
            >
              Yes, Purge All Data
            </AppButton>
            <AppButton
              size="sm"
              variant="ghost"
              :disabled="purging"
              @click="cancelPurge"
            >
              Cancel
            </AppButton>
          </div>
        </div>

        <div v-if="purgeResult?.success" class="space-y-2">
          <AppAlert type="success" :message="purgeResult.message" />
          <div v-if="purgeResult.rows_deleted && Object.keys(purgeResult.rows_deleted).length > 0" class="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div
              v-for="(count, table) in purgeResult.rows_deleted"
              :key="table"
              class="bg-red-50 dark:bg-red-900/20 rounded px-3 py-2"
            >
              <p class="text-xs text-red-600 dark:text-red-400 truncate">{{ table }}</p>
              <p class="text-sm font-medium text-red-800 dark:text-red-300">{{ count.toLocaleString() }} deleted</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Migration form -->
      <div v-if="showMigrateForm" class="border-t border-gray-200 dark:border-gray-700 pt-4 space-y-4">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Migrate to a New Database</h3>

        <AppAlert
          type="info"
          message="This will copy all data from the current database to the target. The current database will not be modified. A restart is required after migration."
        />

        <!-- Connection fields -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <AppSelect
            v-model="dbType"
            label="Database Type"
            :options="dbTypeOptions"
            :disabled="migrating"
          />
          <AppInput
            v-model="host"
            label="Host"
            placeholder="localhost"
            :disabled="migrating"
          />
          <AppInput
            v-model.number="port"
            label="Port"
            type="number"
            :placeholder="dbType === 'postgresql' ? '5432' : '3306'"
            :disabled="migrating"
          />
          <AppInput
            v-model="database"
            label="Database Name"
            placeholder="parsedmarc"
            :disabled="migrating"
          />
          <AppInput
            v-model="username"
            label="Username"
            placeholder="db_user"
            :disabled="migrating"
          />
          <AppInput
            v-model="password"
            label="Password"
            type="password"
            placeholder=""
            :disabled="migrating"
          />
        </div>

        <AppToggle
          v-model="migrateData"
          label="Copy existing data to new database"
          :disabled="migrating"
        />

        <!-- Test result -->
        <AppAlert
          v-if="testMessage"
          :type="testPassed ? 'success' : 'error'"
          :message="testMessage"
        />

        <!-- Migration result -->
        <div v-if="migrateResult?.success" class="space-y-2">
          <AppAlert type="success" :message="migrateResult.message" />
          <div v-if="migrateResult.row_counts && Object.keys(migrateResult.row_counts).length > 0" class="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div
              v-for="(count, table) in migrateResult.row_counts"
              :key="table"
              class="bg-green-50 dark:bg-green-900/20 rounded px-3 py-2"
            >
              <p class="text-xs text-green-600 dark:text-green-400 truncate">{{ table }}</p>
              <p class="text-sm font-medium text-green-800 dark:text-green-300">{{ count.toLocaleString() }} rows</p>
            </div>
          </div>
          <AppAlert
            type="warning"
            message="Restart the application now to use the new database."
          />
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-3">
          <AppButton
            size="sm"
            variant="secondary"
            :loading="testing"
            :disabled="!canTest || migrating"
            @click="handleTestConnection"
          >
            Test Connection
          </AppButton>
          <AppButton
            size="sm"
            :loading="migrating"
            :disabled="!testPassed"
            @click="handleMigrate"
          >
            Migrate &amp; Switch
          </AppButton>
          <AppButton
            size="sm"
            variant="ghost"
            :disabled="migrating"
            @click="cancelMigrate"
          >
            Cancel
          </AppButton>
        </div>
      </div>
    </div>
    <div v-else class="text-sm text-gray-500 dark:text-gray-400">Unable to load database information.</div>
  </AppCard>
</template>
