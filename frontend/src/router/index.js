import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import i18n from '@/i18n'

const { t } = i18n.global

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { titleKey: 'login.title', public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { titleKey: 'menu.dashboard', icon: 'Odometer' },
      },
      {
        path: 'instances',
        name: 'Instances',
        component: () => import('@/views/instances/index.vue'),
        meta: { titleKey: 'menu.instances', icon: 'Monitor' },
      },
      {
        path: 'models',
        name: 'Models',
        component: () => import('@/views/models/index.vue'),
        meta: { titleKey: 'menu.models', icon: 'Cpu' },
      },
      {
        path: 'agents',
        name: 'Agents',
        component: () => import('@/views/agents/index.vue'),
        meta: { titleKey: 'menu.agents', icon: 'UserFilled' },
      },
      {
        path: 'skills',
        name: 'Skills',
        component: () => import('@/views/skills/index.vue'),
        meta: { titleKey: 'menu.skills', icon: 'MagicStick' },
      },
      {
        path: 'outputs',
        name: 'Outputs',
        component: () => import('@/views/outputs/index.vue'),
        meta: { titleKey: 'menu.outputs', icon: 'Document' },
      },
      {
        path: 'memory-pools',
        name: 'MemoryPools',
        component: () => import('@/views/memory-pools/index.vue'),
        meta: { titleKey: 'menu.memoryPools', icon: 'Coin' },
      },
      {
        path: 'collaborations',
        name: 'Collaborations',
        component: () => import('@/views/collaborations/index.vue'),
        meta: { titleKey: 'menu.collaborations', icon: 'Connection' },
      },
      {
        path: 'collaborations/:id/editor',
        name: 'CollaborationEditor',
        component: () => import('@/views/collaborations/editor/index.vue'),
        meta: { titleKey: 'menu.flowEditor', hidden: true },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/index.vue'),
        meta: { titleKey: 'menu.settings', icon: 'Setting', roles: ['admin'] },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard - require auth for non-public routes
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.public) {
    next()
    return
  }
  if (!token) {
    next('/login')
    return
  }
  // Role-based access control
  if (to.meta.roles) {
    try {
      const userStr = localStorage.getItem('user')
      const user = userStr ? JSON.parse(userStr) : null
      if (user && to.meta.roles.includes(user.role)) {
        next()
      } else {
        ElMessage.error(t('login.noPermission'))
        next(from.fullPath || '/dashboard')
      }
    } catch {
      next()
    }
  } else {
    next()
  }
})

export default router
