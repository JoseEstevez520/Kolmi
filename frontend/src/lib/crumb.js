import { ref } from 'vue'

// The last crumb's name, for a screen that names itself (a note, by its title). Empty leaves the
// breadcrumbs with the screen's own default.
export const crumbTitle = ref('')
