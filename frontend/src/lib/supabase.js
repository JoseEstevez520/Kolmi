import { createClient } from '@supabase/supabase-js'

// The anon key is public: it is the key the browser uses for login. The service
// role key is not, and lives only in the backend.
const url = import.meta.env.VITE_SUPABASE_URL || 'https://placeholder.supabase.co'
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'placeholder-anon-key'

if (!import.meta.env.VITE_SUPABASE_URL || !import.meta.env.VITE_SUPABASE_ANON_KEY) {
  console.warn(
    '[kolmi] VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are not set. Copy .env.example to .env.',
  )
}

export const supabase = createClient(url, anonKey)
