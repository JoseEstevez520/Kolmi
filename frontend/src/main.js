import { createApp } from 'vue'
import { ElasticUi } from 'elastic-ui'
import App from './App.vue'
import { i18n, libraryLabels } from './lib/i18n.js'
import router from './router'
import './style.css'

// Mount with the first route already resolved, so the sidebar and the page
// show as they are instead of going through `/` first. The library gets the
// labels object itself, so a language switch can update it in place.
const app = createApp(App).use(i18n).use(router).use(ElasticUi, { labels: libraryLabels })
router.isReady().then(() => app.mount('#app'))
