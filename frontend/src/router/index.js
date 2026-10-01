import { createRouter, createWebHistory } from 'vue-router'
import { authReady, loadProfile, session } from '../lib/auth.js'
import LoginView from '../views/LoginView.vue'
import NotesView from '../views/NotesView.vue'
import RegisterView from '../views/RegisterView.vue'

// After signing in, ask the backend for the profile: a 404 sends the user to
// Register, anything else to Notes.
const routes = [
  { path: '/', redirect: { name: 'notes' } },
  { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
  { path: '/register', name: 'register', component: RegisterView, meta: { public: true } },
  { path: '/notes', name: 'notes', component: NotesView, meta: { layout: 'app' } },
  { path: '/:pathMatch(.*)*', redirect: { name: 'notes' } },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach(async (to) => {
  // Wait for the initial Supabase session before deciding.
  await authReady

  if (!session.value) {
    return to.meta.public ? true : { name: 'login' }
  }

  let current = null
  try {
    current = await loadProfile()
  } catch {
    current = null
  }

  if (!current) {
    return to.name === 'register' ? true : { name: 'register' }
  }
  if (to.name === 'login' || to.name === 'register') {
    return { name: 'notes' }
  }
  return true
})

export default router
