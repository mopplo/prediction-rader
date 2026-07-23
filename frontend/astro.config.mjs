import cloudflare from '@astrojs/cloudflare';
import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://radar.mopplo.com',
  output: 'server',
  adapter: cloudflare({
    platformProxy: {
      enabled: true,
    },
  }),
});
