<script setup lang="ts">
import type { IMAPSettings } from '@/types/mailbox'
import AppInput from '@/components/ui/AppInput.vue'
import AppToggle from '@/components/ui/AppToggle.vue'
import PasswordInput from '@/components/forms/PasswordInput.vue'
import FormSection from '@/components/forms/FormSection.vue'

const model = defineModel<IMAPSettings>({ required: true })

function update<K extends keyof IMAPSettings>(key: K, value: IMAPSettings[K]) {
  model.value = { ...model.value, [key]: value }
}
</script>

<template>
  <FormSection title="IMAP Settings" description="Configure IMAP mailbox connection details.">
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <AppInput
        label="Host"
        :model-value="model.host"
        placeholder="imap.example.com"
        @update:model-value="update('host', $event)"
      />
      <AppInput
        label="Port"
        type="number"
        :model-value="String(model.port)"
        placeholder="993"
        @update:model-value="update('port', Number($event))"
      />
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <AppInput
        label="Username"
        :model-value="model.username"
        placeholder="user@example.com"
        @update:model-value="update('username', $event)"
      />
      <PasswordInput
        label="Password"
        :model-value="model.password"
        placeholder="Enter password"
        @update:model-value="update('password', $event)"
      />
    </div>
    <AppInput
      label="Folder"
      :model-value="model.folder"
      placeholder="INBOX"
      help-text="IMAP folder to watch for DMARC reports."
      @update:model-value="update('folder', $event)"
    />
    <AppInput
      label="Batch Size"
      type="number"
      :model-value="String(model.batch_size)"
      placeholder="10"
      help-text="Number of messages to process per batch."
      @update:model-value="update('batch_size', Number($event))"
    />
    <div class="flex flex-col gap-3">
      <AppToggle
        label="Use SSL/TLS"
        :model-value="model.ssl"
        @update:model-value="update('ssl', $event)"
      />
      <AppToggle
        label="Skip certificate verification"
        :model-value="model.skip_certificate_verification"
        @update:model-value="update('skip_certificate_verification', $event)"
      />
    </div>
  </FormSection>
</template>
