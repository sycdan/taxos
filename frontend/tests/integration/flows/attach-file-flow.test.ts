import { describe, it, expect, afterEach } from "vitest";
import { createTestClient } from "../../utils/api-client";

/**
 * Migrated from backend/tests/test_domain.py: test_attach_file_to_receipt.
 *
 * Verifies that uploading a file via the API works correctly and that
 * duplicate uploads are detected.
 */
describe("File Attachment Flow", () => {
	const apiClient = createTestClient();
	const createdReceiptGuids: string[] = [];

	afterEach(async () => {
		for (const guid of createdReceiptGuids.splice(0)) {
			try {
				await apiClient.deleteReceipt(guid);
			} catch {
				console.warn(`⚠️ Failed to clean up receipt ${guid}`);
			}
		}
	});

	it("should upload a file and detect duplicates", async () => {
		// Create a receipt to reference
		const receipt = await apiClient.createReceipt(
			100.0,
			"Test Vendor",
			"Receipt for file attachment test",
		);
		expect(receipt.guid).toBeDefined();
		createdReceiptGuids.push(receipt.guid);

		// Build a small in-memory file
		const content = new TextEncoder().encode("Test file content for upload");
		const file = new File([content], "test-receipt.txt", {
			type: "text/plain",
		});

		// Compute the SHA-256 hash (mirrors how the frontend does it)
		const hashBuffer = await crypto.subtle.digest(
			"SHA-256",
			await file.arrayBuffer(),
		);
		const fileHash = Array.from(new Uint8Array(hashBuffer))
			.map((b) => b.toString(16).padStart(2, "0"))
			.join("");

		// Upload the file — should succeed on first attempt
		const uploadResult = await apiClient.uploadReceiptFile(file, fileHash);
		expect(uploadResult.alreadyExists).toBe(false);
		expect(uploadResult.fileInfo?.fileHash).toBe(fileHash);

		// Uploading the same file again should report alreadyExists
		const duplicateResult = await apiClient.uploadReceiptFile(file, fileHash);
		expect(duplicateResult.alreadyExists).toBe(true);
	}, 30_000);
});
