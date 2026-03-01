import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', public: true },
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
        meta: { title: '仪表盘', icon: 'Odometer' },
      },
      {
        path: 'instances',
        name: 'Instances',
        component: () => import('@/views/instances/index.vue'),
        meta: { title: '实例管理', icon: 'Monitor' },
      },
      {
        path: 'models',
        name: 'Models',
        component: () => import('@/views/models/index.vue'),
        meta: { title: '模型管理', icon: 'Cpu' },
      },
      {
        path: 'agents',
        name: 'Agents',
        component: () => import('@/views/agents/index.vue'),
        meta: { title: 'Agent管理', icon: 'UserFilled' },
      },
      {
        path: 'skills',
        name: 'Skills',
        component: () => import('@/views/skills/index.vue'),
        meta: { title: 'Skills管理', icon: 'MagicStick' },
      },
      {
        path: 'outputs',
        name: 'Outputs',
        component: () => import('@/views/outputs/index.vue'),
        meta: { title: '输出管理', icon: 'Document' },
      },
      {
        path: 'memory-pools',
        name: 'MemoryPools',
        component: () => import('@/views/memory-pools/index.vue'),
        meta: { title: '共享记忆池', icon: 'Coin' },
      },
      {
        path: 'collaborations',
        name: 'Collaborations',
        component: () => import('@/views/collaborations/index.vue'),
        meta: { title: '协作配置', icon: 'Connection' },
      },
      {
        path: 'collaborations/:id/editor',
        name: 'CollaborationEditor',
        component: () => import('@/views/collaborations/editor/index.vue'),
        meta: { title: '流程编辑器', hidden: true },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/index.vue'),
        meta: { title: '系统设置', icon: 'Setting', roles: ['admin'] },
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
        ElMessage.error('权限不足')
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
