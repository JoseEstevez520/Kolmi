import { createRouter, createWebHistory } from 'vue-router'
import { authReady, loadProfile, session } from '../lib/auth.js'
import AdminLogView from '../views/AdminLogView.vue'
import AdminView from '../views/AdminView.vue'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import NodeView from '../views/NodeView.vue'
import NotesView from '../views/NotesView.vue'
import NoteWriteView from '../views/NoteWriteView.vue'
import RegisterView from '../views/RegisterView.vue'
import ScheduleView from '../views/ScheduleView.vue'
import SettingsView from '../views/SettingsView.vue'

// After signing in, ask the backend for the profile: a 404 sends the user to
// Register, anything else to the home.
const routes = [
  { path: '/', name: 'home', component: HomeView, meta: { layout: 'app' } },
  { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
  { path: '/register', name: 'register', component: RegisterView, meta: { public: true } },
  { path: '/notes', name: 'notes', component: NotesView, meta: { layout: 'app' } },
  // Writing one: a new note (`new`), or one of yours until the daily pass takes it. One route,
  // kept as one page (`meta.page`), so a new note taking its id in the URL doesn't reload it.
  {
    path: '/notes/:id(\\d+|new)',
    name: 'note',
    component: NoteWriteView,
    meta: { layout: 'app', page: 'note' },
  },
  // One screen for a section and one for a page: the node says which.
  { path: '/node/:id', name: 'node', component: NodeView, meta: { layout: 'app' } },
  { path: '/schedule', name: 'schedule', component: ScheduleView, meta: { layout: 'app' } },
  { path: '/settings', name: 'settings', component: SettingsView, meta: { layout: 'app' } },
  { path: '/admin', name: 'admin', component: AdminView, meta: { layout: 'app', admin: true } },
  {
    path: '/admin/log',
    name: 'admin-log',
    component: AdminLogView,
    meta: { layout: 'app', admin: true },
  },
  // Development only: the sample pages of the web agent, drawn with the real renderer.
  ...(import.meta.env.DEV
    ? [
        {
          path: '/dev/pages',
          name: 'dev-pages',
          component: () => import('../views/DevPagesView.vue'),
          meta: { public: true },
        },
      ]
    : []),
  { path: '/:pathMatch(.*)*', redirect: { name: 'home' } },
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
    return { name: 'home' }
  }
  if (to.meta.admin && current.role !== 'admin') {
    return { name: 'home' }
  }
  return true
})

export default router
