import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    name: 'integration',
    environment: 'node',
    testTimeout: 300000, // 5 minutes for debugging
    hookTimeout: 300000, // 5 minutes for debugging
    globals: true,
    setupFiles: ['./tests/integration/setup/global-setup.ts'],
    include: ['tests/integration/**/*.test.ts'],
    exclude: ['node_modules/**'],
    reporter: ['verbose', 'json'],
    outputFile: 'test-results/integration-results.json'
  }
})