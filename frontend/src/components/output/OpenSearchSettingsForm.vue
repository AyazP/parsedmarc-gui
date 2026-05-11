<script setup lang="ts">
import type { OpenSearchSettings } from '@/types/output'
import AppInput from '@/components/ui/AppInput.vue'
import AppToggle from '@/components/ui/AppToggle.vue'
import PasswordInput from '@/components/forms/PasswordInput.vue'
import FormSection from '@/components/forms/FormSection.vue'

const model = defineModel<OpenSearchSettings>({ required: true })

function update<K extends keyof OpenSearchSettings>(key: K, value: OpenSearchSettings[K]) {
  model.value = { ...model.value, [key]: value }
}

function hostsFromString(val: string): string[] {
  return val.split(',').map(s => s.trim()).filter(Boolean)
}
</script>

<template>
  <FormSection title="OpenSearch Settings" description="Configure OpenSearch connection details.">
    <AppInput
      label="Hosts"
      :model-value="model.hosts.join(', ')"
      placeholder="https://localhost:9200"
      help-text="Comma-separated list of OpenSearch hosts."
      @update:model-value="update('hosts', hostsFromString($event))"
    />
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <AppInput
        label="Username"
        :model-value="model.username ?? ''"
        placeholder="admin"
        @update:model-value="update('username', $event || undefined)"
      />
      <PasswordInput
        label="Password"
        :model-value="model.password ?? ''"
        placeholder="Enter password"
        @update:model-value="update('password', $event || undefined)"
      />
    </div>
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
    <AppToggle
      label="Use SSL/TLS"
      :model-value="model.ssl"
      @update:model-value="update('ssl', $event)"
    />
  </FormSection>
</template>
