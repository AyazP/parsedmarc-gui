<script setup lang="ts">
import type { MSGraphSettings } from '@/types/mailbox'
import AppInput from '@/components/ui/AppInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import PasswordInput from '@/components/forms/PasswordInput.vue'
import FormSection from '@/components/forms/FormSection.vue'

const model = defineModel<MSGraphSettings>({ required: true })

const authMethods = [
  { value: 'ClientSecret', label: 'Client Secret (Recommended)' },
  { value: 'DeviceCode', label: 'Device Code' },
  { value: 'UsernamePassword', label: 'Username & Password' },
]

function update<K extends keyof MSGraphSettings>(key: K, value: MSGraphSettings[K]) {
  model.value = { ...model.value, [key]: value }
}
</script>

<template>
  <FormSection title="Microsoft Graph Settings" description="Configure Microsoft 365 mailbox access via Graph API.">
    <AppSelect
      label="Auth Method"
      :model-value="model.auth_method"
      :options="authMethods"
      @update:model-value="update('auth_method', $event as MSGraphSettings['auth_method'])"
    />
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <AppInput
        label="Tenant ID"
        :model-value="model.tenant_id"
        placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        @update:model-value="update('tenant_id', $event)"
      />
      <AppInput
        label="Client ID"
        :model-value="model.client_id"
        placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        @update:model-value="update('client_id', $event)"
      />
    </div>
    <PasswordInput
      v-if="model.auth_method === 'ClientSecret'"
      label="Client Secret"
      :model-value="model.client_secret ?? ''"
      placeholder="Enter client secret"
      @update:model-value="update('client_secret', $event)"
    />
    <template v-if="model.auth_method === 'UsernamePassword'">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <AppInput
          label="Username"
          :model-value="model.username ?? ''"
          placeholder="user@example.com"
          @update:model-value="update('username', $event)"
        />
        <PasswordInput
          label="Password"
          :model-value="model.password ?? ''"
          placeholder="Enter password"
          @update:model-value="update('password', $event)"
        />
      </div>
    </template>
    <AppInput
      label="Mailbox"
      :model-value="model.mailbox"
      placeholder="dmarc@example.com"
      help-text="The mailbox email address to fetch DMARC reports from."
      @update:model-value="update('mailbox', $event)"
    />
    <AppInput
      label="Graph API URL"
      :model-value="model.graph_url"
      placeholder="https://graph.microsoft.com/v1.0"
      help-text="Microsoft Graph API base URL. Change for national clouds."
      @update:model-value="update('graph_url', $event)"
    />
    <AppInput
      label="Batch Size"
      type="number"
      :model-value="String(model.batch_size)"
      placeholder="10"
      @update:model-value="update('batch_size', Number($event))"
    />
  </FormSection>
</template>
