import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
	testDir: "./flows",
	outputDir: "./test-results",
	use: {
		// Frontend container — accessible from the devcontainer via Docker network.
		baseURL: "http://frontend:5173",
		trace: "on-first-retry",
		screenshot: "only-on-failure",
	},
	projects: [
		{
			name: "chromium",
			use: { ...devices["Desktop Chrome"] },
		},
	],
	timeout: 60_000,
	expect: {
		timeout: 10_000,
	},
});
