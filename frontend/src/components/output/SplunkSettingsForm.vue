<script setup lang="ts">
import type { SplunkSettings } from '@/types/output'
import AppInput from '@/components/ui/AppInput.vue'
import AppToggle from '@/components/ui/AppToggle.vue'
import PasswordInput from '@/components/forms/PasswordInput.vue'
import FormSection from '@/components/forms/FormSection.vue'

const model = defineModel<SplunkSettings>({ required: true })

function update<K extends keyof SplunkSettings>(key: K, value: SplunkSettings[K]) {
  model.value = { ...model.value, [key]: value }
}
</script>

<template>
  <FormSection title="Splunk HEC Settings" description="Configure Splunk HTTP Event Collector connection details.">
    <AppInput
      label="HEC URL"
      :model-value="model.url"
      placeholder="https://splunk.example.com:8088"
      @update:model-value="update('url', $event)"
    />
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <PasswordInput
        label="HEC Token"
        :model-value="model.token"
        placeholder="Enter HEC token"
        @update:model-value="update('token', $event)"
      />
      <AppInput
        label="Index"
        :model-value="model.index"
        placeholder="main"
        @update:model-value="update('index', $event)"
      />
    </div>
    <AppToggle
      label="Skip certificate verification"
      :model-value="model.skip_certificate_verification"
      @update:model-value="update('skip_certificate_verification', $event)"
    />
  </FormSection>
</template>
