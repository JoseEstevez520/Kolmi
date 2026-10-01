import { ref } from 'vue'
import { api } from './api.js'

// The module tree the sidebar lists, loaded once and shared. The admin panel
// refreshes it after every change, so the sidebar follows along.
export const modules = ref([])
export const modulesLoading = ref(false)
export const modulesError = ref('')

let loaded = false
let inflight = null

export function loadModules(force = false) {
  if (loaded && !force) return Promise.resolve(modules.value)
  if (inflight) return inflight

  modulesLoading.value = true
  modulesError.value = ''
  inflight = api
    .modules()
    .then((data) => {
      modules.value = Array.isArray(data) ? data : []
      loaded = true
      return modules.value
    })
    .catch((error) => {
      modulesError.value = error.message || 'Could not load the modules.'
      throw error
    })
    .finally(() => {
      modulesLoading.value = false
      inflight = null
    })

  return inflight
}
