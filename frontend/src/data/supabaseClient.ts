import { createClient } from '@supabase/supabase-js';

function normalizeEnvValue(value: string | undefined): string {
  if (!value) {
    return '';
  }

  const trimmed = value.trim();
  if (
    (trimmed.startsWith('"') && trimmed.endsWith('"')) ||
    (trimmed.startsWith("'") && trimmed.endsWith("'"))
  ) {
    return trimmed.slice(1, -1).trim();
  }

  return trimmed;
}

const supabaseUrl = normalizeEnvValue(import.meta.env.VITE_SUPABASE_URL || __APP_SUPABASE_URL__);
const supabaseAnonKey = normalizeEnvValue(
  import.meta.env.VITE_SUPABASE_ANON_KEY ||
    import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ||
    __APP_SUPABASE_ANON_KEY__,
);

export const hasSupabaseConfig = Boolean(supabaseUrl && supabaseAnonKey);

export const supabase = hasSupabaseConfig
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;
