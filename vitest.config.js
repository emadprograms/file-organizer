import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/web/setup.js'],
    testTimeout: 15000
  }
});
