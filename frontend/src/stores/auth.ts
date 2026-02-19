import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<{ username: string } | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const checked = ref(false)

  const isAuthenticated = computed(() => user.value !== null)

  async function login(username: string, password: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      const result = await authApi.login(username, password)
      if (result.success) {
        user.value = result.user
        return true
      }
      error.value = 'Login failed'
      return false
    } catch (e: unknown) {
      const err = e as { detail?: string; message?: string }
      error.value = err.detail || err.message || 'Login failed'
      return false
    } finally {
      loading.value = false
    }
  }

  async function logout(): Promise<void> {
    try {
      await authApi.logout()
    } catch {
      // Ignore errors on logout — clear state regardless
    }
    user.value = null
    checked.value = false
  }

  async function checkAuth(): Promise<void> {
    if (checked.value) return
    try {
      const result = await authApi.me()
      user.value = { username: result.username }
    } catch {
      user.value = null
    }
    checked.value = true
  }

  return {
    user,
    loading,
    error,
    checked,
    isAuthenticated,
    login,
    logout,
    checkAuth,
  }
})
