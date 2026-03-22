import { beforeAll, afterAll } from "vitest";
import { createTestClient } from "../../utils/api-client";

const apiClient = createTestClient();
let preExistingBucketGuids = new Set<string>();

beforeAll(async () => {
	console.log("🚀 Setting up integration test environment...");

	// Wait for backend to be ready by testing ListBuckets
	const maxRetries = 5;
	let retries = 0;

	while (retries < maxRetries) {
		try {
			console.log(
				`⏳ Attempt ${retries + 1}/${maxRetries} to connect to backend...`,
			);
			const result = await apiClient.getDashboard();
			console.log(
				"✅ Backend is ready, received:",
				JSON.stringify(result).slice(0, 100),
			);
			preExistingBucketGuids = new Set(
				(result.buckets ?? []).map((b: { guid: string }) => b.guid),
			);
			console.log(
				`📋 Snapshotted ${preExistingBucketGuids.size} pre-existing bucket(s)`,
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

	try {
		const dashboard = await apiClient.getDashboard();
		const remainingBuckets: Array<{ guid: string }> = dashboard.buckets ?? [];
		const toDelete = remainingBuckets.filter(
			(b) => !preExistingBucketGuids.has(b.guid),
		);

		if (toDelete.length === 0) {
			console.log("✅ No leftover test buckets to clean up");
			return;
		}

		console.log(`🗑️  Cleaning up ${toDelete.length} leftover test bucket(s)...`);
		let cleaned = 0;
		for (const bucket of toDelete) {
			try {
				await apiClient.deleteBucket(bucket.guid);
				cleaned++;
			} catch {
				console.warn(`⚠️ Failed to clean up bucket ${bucket.guid}`);
			}
		}
		console.log(
			`✅ Cleaned up ${cleaned} / ${toDelete.length} leftover test bucket(s)`,
		);
	} catch (error) {
		console.warn("⚠️ Global cleanup failed:", error);
	}
});
