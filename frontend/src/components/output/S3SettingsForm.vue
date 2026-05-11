<script setup lang="ts">
import type { S3Settings } from '@/types/output'
import AppInput from '@/components/ui/AppInput.vue'
import PasswordInput from '@/components/forms/PasswordInput.vue'
import FormSection from '@/components/forms/FormSection.vue'

const model = defineModel<S3Settings>({ required: true })

function update<K extends keyof S3Settings>(key: K, value: S3Settings[K]) {
  model.value = { ...model.value, [key]: value }
}
</script>

<template>
  <FormSection title="Amazon S3 Settings" description="Configure Amazon S3 bucket connection details.">
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <AppInput
        label="Bucket"
        :model-value="model.bucket"
        placeholder="my-dmarc-reports"
        @update:model-value="update('bucket', $event)"
      />
      <AppInput
        label="Region"
        :model-value="model.region"
        placeholder="us-east-1"
        @update:model-value="update('region', $event)"
      />
    </div>
    <AppInput
      label="Key Prefix"
      :model-value="model.prefix ?? ''"
      placeholder="Optional object key prefix (e.g. dmarc/)"
      @update:model-value="update('prefix', $event || undefined)"
    />
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <AppInput
        label="Access Key ID"
        :model-value="model.access_key_id ?? ''"
        placeholder="Optional — uses IAM role if blank"
        @update:model-value="update('access_key_id', $event || undefined)"
      />
      <PasswordInput
        label="Secret Access Key"
        :model-value="model.secret_access_key ?? ''"
        placeholder="Optional — uses IAM role if blank"
        @update:model-value="update('secret_access_key', $event || undefined)"
      />
    </div>
  </FormSection>
</template>
