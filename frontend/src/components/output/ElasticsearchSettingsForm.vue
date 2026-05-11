<script setup lang="ts">
import type { ElasticsearchSettings } from '@/types/output'
import AppInput from '@/components/ui/AppInput.vue'
import AppToggle from '@/components/ui/AppToggle.vue'
import PasswordInput from '@/components/forms/PasswordInput.vue'
import FormSection from '@/components/forms/FormSection.vue'

const model = defineModel<ElasticsearchSettings>({ required: true })

function update<K extends keyof ElasticsearchSettings>(key: K, value: ElasticsearchSettings[K]) {
  model.value = { ...model.value, [key]: value }
}

function hostsFromString(val: string): string[] {
  return val.split(',').map(s => s.trim()).filter(Boolean)
}
</script>

<template>
  <FormSection title="Elasticsearch Settings" description="Configure Elasticsearch connection details.">
    <AppInput
      label="Hosts"
      :model-value="model.hosts.join(', ')"
      placeholder="https://localhost:9200"
      help-text="Comma-separated list of Elasticsearch hosts."
      @update:model-value="update('hosts', hostsFromString($event))"
    />
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <AppInput
        label="Username"
        :model-value="model.username ?? ''"
        placeholder="elastic"
        @update:model-value="update('username', $event || undefined)"
      />
      <PasswordInput
        label="Password"
        :model-value="model.password ?? ''"
        placeholder="Enter password"
        @update:model-value="update('password', $event || undefined)"
      />
    </div>
    <AppInput
      label="API Key"
      :model-value="model.api_key ?? ''"
      placeholder="Optional API key (base64-encoded id:api_key)"
      @update:model-value="update('api_key', $event || undefined)"
    />
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <AppInput
        label="Index Suffix"
        :model-value="model.index_suffix ?? ''"
        placeholder="Optional index name suffix"
        @update:model-value="update('index_suffix', $event || undefined)"
      />
      <AppInput
        label="CA Certificate Path"
        :model-value="model.cert_path ?? ''"
        placeholder="/path/to/ca.crt"
        @update:model-value="update('cert_path', $event || undefined)"
      />
    </div>
    <div class="flex flex-col gap-3">
      <AppToggle
        label="Use SSL/TLS"
        :model-value="model.ssl"
        @update:model-value="update('ssl', $event)"
      />
      <AppToggle
        label="Use monthly indexes"
        :model-value="model.monthly_indexes"
        @update:model-value="update('monthly_indexes', $event)"
      />
    </div>
  </FormSection>
</template>
