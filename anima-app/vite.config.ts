import { defineConfig } from 'vite';
import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { VitePWA } from 'vite-plugin-pwa';

const root = dirname(fileURLToPath(import.meta.url));
const pub = (f: string) => join(root, 'public', f);
const has192 = existsSync(pub('icon-192.png'));
const has512 = existsSync(pub('icon-512.png'));
const hasApple = existsSync(pub('apple-touch-icon.png'));

const icons: any[] = [];
if (has192) icons.push({ src: 'icon-192.png', sizes: '192x192', type: 'image/png' });
if (has512) {
  icons.push({ src: 'icon-512.png', sizes: '512x512', type: 'image/png' });
  icons.push({ src: 'icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' });
}
icons.push({ src: 'icon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any maskable' });

const includeAssets = ['icon.svg',
  ...(has192 ? ['icon-192.png'] : []),
  ...(has512 ? ['icon-512.png'] : []),
  ...(hasApple ? ['apple-touch-icon.png'] : []),
];

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets,
      manifest: {
        name: 'Motif — a calm companion that notices the patterns of your life',
        short_name: 'Motif',
        description: 'A wise wellness companion that helps you feel, breathe, and heal.',
        theme_color: '#13132B',
        background_color: '#13132B',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons,
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,woff,woff2}'],
        navigateFallback: '/index.html',
        navigateFallbackDenylist: [new RegExp('^/api/')],
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } },
  },
});
