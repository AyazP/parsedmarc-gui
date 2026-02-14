import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useSetupStore } from '@/stores/setup'

const routes: RouteRecordRaw[] = [
  {
    path: '/setup',
    name: 'setup',
    component: () => import('@/views/setup/SetupWizard.vue'),
    meta: { layout: 'blank' },
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

  return true
})

export default router
