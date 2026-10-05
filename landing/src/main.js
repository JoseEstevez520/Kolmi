import { createApp } from 'vue'
import { ElasticUi } from 'elastic-ui'
import App from './App.vue'
import { libraryLabels } from './i18n.js'
import './style.css'

// The library gets the labels object itself, so a language switch updates it in place.
createApp(App).use(ElasticUi, { labels: libraryLabels }).mount('#app')
