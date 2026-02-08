import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    name: 'integration',
    environment: 'node',
    testTimeout: 30000,
    hookTimeout: 30000,
    globals: true,
    setupFiles: ['./tests/integration/setup/global-setup.ts'],
    include: ['tests/integration/**/*.test.ts'],
    exclude: ['node_modules/**'],
    reporter: ['verbose', 'json'],
    outputFile: 'test-results/integration-results.json'
  }
})