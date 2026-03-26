import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Writing',
    component: () => import('@/views/Writing.vue')
  },
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: () => import('@/views/Knowledge.vue')
  },
  {
    path: '/templates',
    name: 'Templates',
    component: () => import('@/views/Templates.vue')
  },
  {
    path: '/documents',
    name: 'Documents',
    component: () => import('@/views/Documents.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router