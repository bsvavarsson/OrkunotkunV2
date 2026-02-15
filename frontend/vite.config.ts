import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const rootEnv = loadEnv(mode, '..', '');
  const supabaseUrl = rootEnv.VITE_SUPABASE_URL || rootEnv.SUPABASE_API_URL || '';
  const supabaseAnonKey = rootEnv.VITE_SUPABASE_ANON_KEY || rootEnv.SUPABASE_ANON_KEY || '';

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
