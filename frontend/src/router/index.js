import { createRouter, createWebHistory } from 'vue-router'
import { chatEnabled, loadChatEnabled } from '../lib/chat.js'
import { authReady, isWaiting, loadProfile, session } from '../lib/auth.js'
import AdminLogView from '../views/AdminLogView.vue'
import AdminClassView from '../views/AdminClassView.vue'
import AdminContentView from '../views/AdminContentView.vue'
import AdminPeopleView from '../views/AdminPeopleView.vue'
import ChatView from '../views/ChatView.vue'
import AdminView from '../views/AdminView.vue'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import NodeView from '../views/NodeView.vue'
import NotesView from '../views/NotesView.vue'
import NoteWriteView from '../views/NoteWriteView.vue'
import RegisterView from '../views/RegisterView.vue'
import ScheduleView from '../views/ScheduleView.vue'
import SettingsView from '../views/SettingsView.vue'
import WaitingView from '../views/WaitingView.vue'

// After signing in, ask the backend for the profile: a 404 sends the user to
// Register, anything else to the home.
const routes = [
  { path: '/', name: 'home', component: HomeView, meta: { layout: 'app' } },
  { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
  { path: '/register', name: 'register', component: RegisterView, meta: { public: true } },
  // Signed in but not let in (pending or blocked): the only screen such a person gets. It needs a
  // session, so it is not public, and it has no sidebar.
  { path: '/waiting', name: 'waiting', component: WaitingView },
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
  // The conversation full screen: the same one as the bubble's (lib/chat.js). Only where the
  // admin turned the chat on.
  { path: '/chat', name: 'chat', component: ChatView, meta: { layout: 'app', chat: true, fullBleed: true } },
  { path: '/schedule', name: 'schedule', component: ScheduleView, meta: { layout: 'app' } },
  { path: '/settings', name: 'settings', component: SettingsView, meta: { layout: 'app' } },
  // The admin panel is three pages under one shell (title and selector): /admin itself is the
  // content, so old links and `{ name: 'admin' }` keep working. `meta.page` keeps the shell
  // still while the pages inside it change.
  {
    path: '/admin',
    component: AdminView,
    meta: { layout: 'app', admin: true, page: 'admin' },
    children: [
      { path: '', name: 'admin', redirect: { name: 'admin-content' } },
      { path: 'content', name: 'admin-content', component: AdminContentView },
      { path: 'people', name: 'admin-people', component: AdminPeopleView },
      { path: 'class', name: 'admin-class', component: AdminClassView },
    ],
  },
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
  // Someone waiting or blocked reaches nothing but the waiting screen and login.
  if (isWaiting(current)) {
    return to.name === 'waiting' || to.name === 'login' ? true : { name: 'waiting' }
  }
  if (to.name === 'waiting' || to.name === 'login' || to.name === 'register') {
    return { name: 'home' }
  }
  if (to.meta.admin && current.role !== 'admin') {
    return { name: 'home' }
  }
  if (to.meta.chat) {
    if (chatEnabled.value === null) await loadChatEnabled()
    if (!chatEnabled.value) return { name: 'home' }
  }
  return true
})

export default router
