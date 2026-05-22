import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { title: '仪表盘', requiresAuth: true },
  },
  {
    path: '/departments',
    name: 'Departments',
    component: () => import('../views/Departments.vue'),
    meta: { title: '部门管理', requiresAuth: true, roles: ['super_admin'] },
  },
  {
    path: '/employees',
    name: 'Employees',
    component: () => import('../views/Employees.vue'),
    meta: { title: '人员管理', requiresAuth: true, roles: ['super_admin', 'dept_manager'] },
  },
  {
    path: '/checkin',
    name: 'Checkin',
    component: () => import('../views/Checkin.vue'),
    meta: { title: '签到系统', requiresAuth: true },
  },
  {
    path: '/orgchart',
    name: 'OrgChart',
    component: () => import('../views/OrgChart.vue'),
    meta: { title: '组织架构', requiresAuth: true },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue'),
    meta: { title: '系统设置', requiresAuth: true, roles: ['super_admin'] },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard — check auth
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || 'null')

  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }

  if (to.meta.roles && user) {
    if (!to.meta.roles.includes(user.role)) {
      return next('/')  // Redirect to dashboard if no permission
    }
  }

  if (to.path === '/login' && token) {
    return next('/')
  }

  next()
})

export default router
