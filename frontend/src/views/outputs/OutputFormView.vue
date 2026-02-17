<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useOutputStore } from '@/stores/outputs'
import { useToast } from '@/composables/useToast'
import type {
  OutputType,
  ElasticsearchSettings,
  OpenSearchSettings,
  SplunkSettings,
  KafkaSettings,
  S3Settings,
  SyslogSettings,
  GELFSettings,
  WebhookSettings,
  OutputConfigCreate,
  OutputConfigUpdate,
} from '@/types/output'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppToggle from '@/components/ui/AppToggle.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppAlert from '@/components/ui/AppAlert.vue'
import ElasticsearchSettingsForm from '@/components/output/ElasticsearchSettingsForm.vue'
import OpenSearchSettingsForm from '@/components/output/OpenSearchSettingsForm.vue'
import SplunkSettingsForm from '@/components/output/SplunkSettingsForm.vue'
import KafkaSettingsForm from '@/components/output/KafkaSettingsForm.vue'
import S3SettingsForm from '@/components/output/S3SettingsForm.vue'
import SyslogSettingsForm from '@/components/output/SyslogSettingsForm.vue'
import GelfSettingsForm from '@/components/output/GelfSettingsForm.vue'
import WebhookSettingsForm from '@/components/output/WebhookSettingsForm.vue'

const route = useRoute()
const router = useRouter()
const store = useOutputStore()
const toast = useToast()

const editId = computed(() => {
  const id = route.params.id
  return id ? Number(id) : null
})
const isEdit = computed(() => editId.value !== null)
const pageLoading = ref(false)
const saving = ref(false)
const formError = ref<string | null>(null)

// Form state
const name = ref('')
const type = ref<OutputType>('elasticsearch')
const enabled = ref(true)
const saveAggregate = ref(true)
const saveForensic = ref(true)
const saveSmtpTls = ref(true)

const elasticsearchSettings = ref<ElasticsearchSettings>({
  hosts: ['https://localhost:9200'],
  ssl: true,
  monthly_indexes: false,
})

const opensearchSettings = ref<OpenSearchSettings>({
  hosts: ['https://localhost:9200'],
  ssl: true,
})

const splunkSettings = ref<SplunkSettings>({
  url: '',
  token: '',
  index: 'main',
  skip_certificate_verification: false,
})

const kafkaSettings = ref<KafkaSettings>({
  servers: ['localhost:9092'],
  aggregate_topic: 'dmarc_aggregate',
  forensic_topic: 'dmarc_forensic',
  smtp_tls_topic: 'smtp_tls',
  ssl: false,
})

const s3Settings = ref<S3Settings>({
  bucket: '',
  region: 'us-east-1',
})

const syslogSettings = ref<SyslogSettings>({
  server: 'localhost',
  port: 514,
})

const gelfSettings = ref<GELFSettings>({
  server: 'localhost',
  port: 12201,
})

const webhookSettings = ref<WebhookSettings>({
  url: '',
  timeout: 30,
})

const typeOptions = [
  { value: 'elasticsearch', label: 'Elasticsearch' },
  { value: 'opensearch', label: 'OpenSearch' },
  { value: 'splunk', label: 'Splunk HEC' },
  { value: 'kafka', label: 'Apache Kafka' },
  { value: 's3', label: 'Amazon S3' },
  { value: 'syslog', label: 'Syslog' },
  { value: 'gelf', label: 'GELF (Graylog)' },
  { value: 'webhook', label: 'Webhook' },
]

onMounted(async () => {
  if (!isEdit.value) return
  pageLoading.value = true
  try {
    const config = await store.getConfig(editId.value!)
    if (!config) {
      toast.error('Output config not found.')
      router.replace('/outputs')
      return
    }
    name.value = config.name
    type.value = config.type
    enabled.value = config.enabled
    saveAggregate.value = config.save_aggregate
    saveForensic.value = config.save_forensic
    saveSmtpTls.value = config.save_smtp_tls

    const settingsMap: Record<OutputType, { ref: { value: unknown }; data: Record<string, unknown> | undefined }> = {
      elasticsearch: { ref: elasticsearchSettings, data: config.elasticsearch_settings },
      opensearch: { ref: opensearchSettings, data: config.opensearch_settings },
      splunk: { ref: splunkSettings, data: config.splunk_settings },
      kafka: { ref: kafkaSettings, data: config.kafka_settings },
      s3: { ref: s3Settings, data: config.s3_settings },
      syslog: { ref: syslogSettings, data: config.syslog_settings },
      gelf: { ref: gelfSettings, data: config.gelf_settings },
      webhook: { ref: webhookSettings, data: config.webhook_settings },
    }

    const entry = settingsMap[config.type]
    if (entry.data) {
      entry.ref.value = { ...entry.ref.value as Record<string, unknown>, ...entry.data }
    }
  } catch {
    toast.error('Failed to load output config.')
    router.replace('/outputs')
  } finally {
    pageLoading.value = false
  }
})

function getTypeSettings(): Record<string, unknown> {
  const settingsMap: Record<OutputType, Record<string, unknown>> = {
    elasticsearch: { elasticsearch_settings: elasticsearchSettings.value },
    opensearch: { opensearch_settings: opensearchSettings.value },
    splunk: { splunk_settings: splunkSettings.value },
    kafka: { kafka_settings: kafkaSettings.value },
    s3: { s3_settings: s3Settings.value },
    syslog: { syslog_settings: syslogSettings.value },
    gelf: { gelf_settings: gelfSettings.value },
    webhook: { webhook_settings: webhookSettings.value },
  }
  return settingsMap[type.value]
}

async function handleSubmit() {
  formError.value = null

  if (!name.value.trim()) {
    formError.value = 'Name is required.'
    return
  }

  saving.value = true
  try {
    if (isEdit.value) {
      const data: OutputConfigUpdate = {
        name: name.value,
        enabled: enabled.value,
        save_aggregate: saveAggregate.value,
        save_forensic: saveForensic.value,
        save_smtp_tls: saveSmtpTls.value,
        ...getTypeSettings(),
      }
      await store.updateConfig(editId.value!, data)
      toast.success('Output config updated.')
    } else {
      const data: OutputConfigCreate = {
        name: name.value,
        type: type.value,
        enabled: enabled.value,
        save_aggregate: saveAggregate.value,
        save_forensic: saveForensic.value,
        save_smtp_tls: saveSmtpTls.value,
        ...getTypeSettings(),
      }
      await store.createConfig(data)
      toast.success('Output config created.')
    }
    router.push('/outputs')
  } catch (e: unknown) {
    const err = e as { detail?: string; message?: string }
    formError.value = err.detail || err.message || 'Failed to save output config.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <AppButton variant="ghost" @click="router.push('/outputs')">
        &larr; Back
      </AppButton>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">
        {{ isEdit ? 'Edit Output' : 'New Output' }}
      </h1>
    </div>

    <div v-if="pageLoading" class="flex justify-center py-12">
      <AppSpinner size="lg" />
    </div>

    <form v-else class="space-y-6" @submit.prevent="handleSubmit">
      <AppAlert v-if="formError" variant="error" :message="formError" dismissible @dismiss="formError = null" />

      <AppCard>
        <template #header>
          <h2 class="text-base font-semibold text-gray-900 dark:text-gray-100">General</h2>
        </template>
        <div class="space-y-4">
          <AppInput
            label="Name"
            v-model="name"
            placeholder="My Elasticsearch Output"
          />
          <AppSelect
            label="Type"
            :model-value="type"
            :options="typeOptions"
            :disabled="isEdit"
            @update:model-value="type = $event as OutputType"
          />
          <div class="flex flex-col gap-3">
            <AppToggle v-model="enabled" label="Enabled" />
            <AppToggle v-model="saveAggregate" label="Save aggregate reports" />
            <AppToggle v-model="saveForensic" label="Save forensic reports" />
            <AppToggle v-model="saveSmtpTls" label="Save SMTP TLS reports" />
          </div>
        </div>
      </AppCard>

      <AppCard>
        <ElasticsearchSettingsForm v-if="type === 'elasticsearch'" v-model="elasticsearchSettings" />
        <OpenSearchSettingsForm v-else-if="type === 'opensearch'" v-model="opensearchSettings" />
        <SplunkSettingsForm v-else-if="type === 'splunk'" v-model="splunkSettings" />
        <KafkaSettingsForm v-else-if="type === 'kafka'" v-model="kafkaSettings" />
        <S3SettingsForm v-else-if="type === 's3'" v-model="s3Settings" />
        <SyslogSettingsForm v-else-if="type === 'syslog'" v-model="syslogSettings" />
        <GelfSettingsForm v-else-if="type === 'gelf'" v-model="gelfSettings" />
        <WebhookSettingsForm v-else-if="type === 'webhook'" v-model="webhookSettings" />
      </AppCard>

      <div class="flex justify-end gap-3">
        <AppButton variant="secondary" @click="router.push('/outputs')">Cancel</AppButton>
        <AppButton type="submit" :loading="saving">
          {{ isEdit ? 'Save Changes' : 'Create Output' }}
        </AppButton>
      </div>
    </form>
  </div>
</template>
