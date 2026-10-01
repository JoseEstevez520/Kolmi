import { createRouter, createWebHistory } from 'vue-router'
import { authReady, loadProfile, session } from '../lib/auth.js'
import AdminView from '../views/AdminView.vue'
import LoginView from '../views/LoginView.vue'
import NotesView from '../views/NotesView.vue'
import PageView from '../views/PageView.vue'
import RegisterView from '../views/RegisterView.vue'
import SectionView from '../views/SectionView.vue'

// After signing in, ask the backend for the profile: a 404 sends the user to
// Register, anything else to Notes.
const routes = [
  { path: '/', redirect: { name: 'notes' } },
  { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
  { path: '/register', name: 'register', component: RegisterView, meta: { public: true } },
  { path: '/notes', name: 'notes', component: NotesView, meta: { layout: 'app' } },
  {
    path: '/sections/:sectionId',
    name: 'section',
    component: SectionView,
    meta: { layout: 'app' },
  },
  {
    path: '/sections/:sectionId/pages/:pageId',
    name: 'page',
    component: PageView,
    meta: { layout: 'app' },
  },
  { path: '/admin', name: 'admin', component: AdminView, meta: { layout: 'app', admin: true } },
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
  if (to.meta.admin && current.role !== 'admin') {
    return { name: 'notes' }
  }
  return true
})

export default router
