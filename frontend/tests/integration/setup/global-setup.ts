import { beforeAll, afterAll } from "vitest";
import { createTestClient } from "../../utils/api-client";

beforeAll(async () => {
	console.log("🚀 Setting up integration test environment...");

	// Wait for backend to be ready by testing ListBuckets
	const maxRetries = 5;
	let retries = 0;
	const apiClient = createTestClient();

	while (retries < maxRetries) {
		try {
			console.log(
				`⏳ Attempt ${retries + 1}/${maxRetries} to connect to backend...`,
			);
			const result = await apiClient.listBuckets();
			console.log(
				"✅ Backend is ready, received:",
				JSON.stringify(result).slice(0, 100),
			);
			break;
		} catch (error) {
			console.log(
				`❌ Connection attempt ${retries + 1} failed:`,
				error instanceof Error ? error.message : String(error),
			);
			retries++;
			if (retries === maxRetries) {
				console.error("❌ Backend server not available after 5 retries");
				throw new Error(
					`Backend server not available after ${maxRetries} retries: ${error}`,
				);
			}
			await new Promise((resolve) => setTimeout(resolve, 3000));
		}
	}
}, 300000); // 5 minutes for debugging

afterAll(async () => {
	console.log("🧹 Cleaning up integration test environment...");
});
