import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useSetupStore } from '@/stores/setup'
import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    layout?: 'app' | 'blank'
    public?: boolean
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { layout: 'blank', public: true },
  },
  {
    path: '/setup',
    name: 'setup',
    component: () => import('@/views/setup/SetupWizard.vue'),
    meta: { layout: 'blank', public: true },
  },
  {
    path: '/',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { layout: 'app' },
  },
  {
    path: '/mailboxes',
    name: 'mailboxes',
    component: () => import('@/views/mailboxes/MailboxListView.vue'),
    meta: { layout: 'app' },
  },
  {
    path: '/mailboxes/new',
    name: 'mailbox-create',
    component: () => import('@/views/mailboxes/MailboxFormView.vue'),
    meta: { layout: 'app' },
  },
  {
    path: '/mailboxes/:id/edit',
    name: 'mailbox-edit',
    component: () => import('@/views/mailboxes/MailboxFormView.vue'),
    meta: { layout: 'app' },
  },
  {
    path: '/outputs',
    name: 'outputs',
    component: () => import('@/views/outputs/OutputListView.vue'),
    meta: { layout: 'app' },
  },
  {
    path: '/outputs/new',
    name: 'output-create',
    component: () => import('@/views/outputs/OutputFormView.vue'),
    meta: { layout: 'app' },
  },
  {
    path: '/outputs/:id/edit',
    name: 'output-edit',
    component: () => import('@/views/outputs/OutputFormView.vue'),
    meta: { layout: 'app' },
  },
  {
    path: '/reports',
    name: 'reports',
    component: () => import('@/views/reports/ReportListView.vue'),
    meta: { layout: 'app' },
  },
  {
    path: '/reports/:id',
    name: 'report-detail',
    component: () => import('@/views/reports/ReportDetailView.vue'),
    meta: { layout: 'app' },
  },
  {
    path: '/jobs',
    name: 'jobs',
    component: () => import('@/views/jobs/JobListView.vue'),
    meta: { layout: 'app' },
  },
  {
    path: '/upload',
    name: 'upload',
    component: () => import('@/views/upload/FileUploadView.vue'),
    meta: { layout: 'app' },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/settings/SettingsView.vue'),
    meta: { layout: 'app' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  // 1. Setup check — must run first (no auth before setup is complete)
  const setupStore = useSetupStore()

  if (setupStore.status === null) {
    try {
      await setupStore.fetchStatus()
    } catch {
      return true
    }
  }

  if (setupStore.needsSetup && to.name !== 'setup') {
    return { name: 'setup' }
  }

  if (!setupStore.needsSetup && to.name === 'setup') {
    return { name: 'dashboard' }
  }

  // 2. Auth check — skip for public routes
  if (!to.meta.public) {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated) {
      await authStore.checkAuth()
      if (!authStore.isAuthenticated) {
        return { name: 'login', query: { redirect: to.fullPath } }
      }
    }
  }

  // 3. Redirect authenticated users away from login
  if (to.name === 'login') {
    const authStore = useAuthStore()
    if (authStore.isAuthenticated) {
      return { name: 'dashboard' }
    }
  }

  return true
})

export default router
