<script setup lang="ts">
import type { GmailSettings } from '@/types/mailbox'
import AppInput from '@/components/ui/AppInput.vue'
import AppToggle from '@/components/ui/AppToggle.vue'
import FormSection from '@/components/forms/FormSection.vue'

const model = defineModel<GmailSettings>({ required: true })

function update<K extends keyof GmailSettings>(key: K, value: GmailSettings[K]) {
  model.value = { ...model.value, [key]: value }
}
</script>

<template>
  <FormSection title="Gmail Settings" description="Configure Gmail access via OAuth2.">
    <AppInput
      label="Credentials File"
      :model-value="model.credentials_file"
      placeholder="/path/to/credentials.json"
      help-text="Path to the Google OAuth2 credentials JSON file."
      @update:model-value="update('credentials_file', $event)"
    />
    <AppInput
      label="Token File"
      :model-value="model.token_file ?? ''"
      placeholder="Optional — auto-generated"
      help-text="Path to store the OAuth2 token. Leave empty for auto-generated path."
      @update:model-value="update('token_file', $event || undefined)"
    />
    <AppInput
      label="Scopes (comma-separated)"
      :model-value="model.scopes.join(', ')"
      placeholder="https://www.googleapis.com/auth/gmail.modify"
      help-text="OAuth2 scopes. Default is gmail.modify."
      @update:model-value="update('scopes', $event.split(',').map((s: string) => s.trim()).filter(Boolean))"
    />
    <AppInput
      label="Batch Size"
      type="number"
      :model-value="String(model.batch_size)"
      placeholder="10"
      @update:model-value="update('batch_size', Number($event))"
    />
    <AppToggle
      label="Include Spam & Trash"
      :model-value="model.include_spam_trash"
      @update:model-value="update('include_spam_trash', $event)"
    />
  </FormSection>
</template>
