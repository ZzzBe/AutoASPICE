import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('../views/dashboard/DashboardPage.vue'),
    meta: { title: 'Dashboard' }
  },
  {
    path: '/project/:id',
    component: () => import('../views/project/ProjectPage.vue'),
    meta: { title: 'Project' }
  },
  {
    path: '/agents',
    component: () => import('../views/agent/AgentMarket.vue'),
    meta: { title: 'Agent Market' }
  },
  {
    path: '/audit/:projectId',
    component: () => import('../views/audit/AuditDashboard.vue'),
    meta: { title: 'Audit Trail' }
  },
  {
    path: '/settings',
    component: () => import('../views/settings/SettingsPage.vue'),
    meta: { title: 'Settings' }
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.afterEach((to) => {
  document.title = `${to.meta.title || 'AutoDev Studio'} - AutoDev Studio`
})

export default router
