import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const normalizeEnvValue = (value: string | undefined): string => {
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
  };

  const rootEnv = loadEnv(mode, '..', '');
  const supabaseUrl = normalizeEnvValue(rootEnv.VITE_SUPABASE_URL || rootEnv.SUPABASE_API_URL || '');
  const supabaseAnonKey = normalizeEnvValue(
    rootEnv.VITE_SUPABASE_ANON_KEY ||
      rootEnv.SUPABASE_ANON_KEY ||
      rootEnv.VITE_SUPABASE_PUBLISHABLE_KEY ||
      rootEnv.SUPABASE_PUBLISHABLE_KEY ||
      '',
  );

  return {
    plugins: [react()],
    envDir: '..',
    define: {
      __APP_SUPABASE_URL__: JSON.stringify(supabaseUrl),
      __APP_SUPABASE_ANON_KEY__: JSON.stringify(supabaseAnonKey),
    },
    server: {
      port: 5173,
    },
  };
});
