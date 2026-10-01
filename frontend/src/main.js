import { createApp } from 'vue'
import { ElasticUi } from 'elastic-ui'
import App from './App.vue'
import router from './router'
import './style.css'

// Mount with the first route already resolved, so the sidebar and the page
// show as they are instead of going through `/` first.
const app = createApp(App).use(router).use(ElasticUi)
router.isReady().then(() => app.mount('#app'))
