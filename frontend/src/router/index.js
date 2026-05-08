import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/RegisterView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'dashboard', component: () => import('../views/DashboardView.vue') },
      { path: 'scenarios', name: 'scenarios', component: () => import('../views/ScenarioView.vue') },
      { path: 'scenarios/:id', name: 'scenario-detail', component: () => import('../views/ScenarioDetailView.vue') },
      { path: 'simulations', name: 'simulation-list', component: () => import('../views/SimulationListView.vue') },
      { path: 'simulations/new', name: 'simulation-new', component: () => import('../views/SimulationView.vue') },
      { path: 'simulations/:id', name: 'simulation', component: () => import('../views/SimulationView.vue') },
      { path: 'messages', name: 'messages', component: () => import('../views/MessagePolishView.vue') },
      { path: 'patterns', name: 'patterns', component: () => import('../views/PatternView.vue') },
      { path: 'relationships', name: 'relationships', component: () => import('../views/RelationshipView.vue') },
      { path: 'relationships/:id', name: 'relationship-detail', component: () => import('../views/RelationshipDetailView.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: 'login' }
  }

  if (to.meta.public && auth.isLoggedIn && to.name !== 'dashboard') {
    return { name: 'dashboard' }
  }

  if (auth.isLoggedIn && !auth.user) {
    await auth.fetchUser()
  }
})

export default router