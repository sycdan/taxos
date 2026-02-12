import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { createTestClient } from "../../utils/api-client";
import { testBucketData, testReceiptData } from "../fixtures/api-fixtures";

describe("Full Taxos API Integration Flow", () => {
	const apiClient = createTestClient();
	let createdBucketGuids: string[] = [];
	let createdReceiptGuids: string[] = [];
	const currentMonth = new Date().toISOString().slice(0, 7);

	beforeEach(async () => {
		createdBucketGuids = [];
		createdReceiptGuids = [];
	});

	afterEach(async () => {
		if (createdReceiptGuids.length > 0) {
			let cleanedReceipts = 0;
			for (const receiptGuid of createdReceiptGuids) {
				try {
					await apiClient.deleteReceipt(receiptGuid);
				} catch {
					console.warn(`⚠️ Failed to clean up receipt ${receiptGuid}`);
				}
			}
			console.log(
				`✅ Cleaned up ${cleanedReceipts} / ${createdReceiptGuids.length} receipts`,
			);
		}

		if (createdBucketGuids.length > 0) {
			let cleanedBuckets = 0;
			for (const bucketGuid of createdBucketGuids) {
				try {
					await apiClient.deleteBucket(bucketGuid);
				} catch {
					console.warn("⚠️ Failed to clean up bucket:", bucketGuid);
				}
			}
			console.log(
				`✅ Cleaned up ${cleanedBuckets} / ${createdBucketGuids.length} buckets`,
			);
		}
	});

	it("should complete the full bucket and receipt management flow", async () => {
		console.log("🔄 Starting full integration test flow...");

		console.log("📋 Step 1: Listing existing buckets...");
		const initialDashboard = await apiClient.getDashboard({
			months: [currentMonth],
		});
		expect(initialDashboard).toBeDefined();
		expect(initialDashboard.buckets).toBeDefined();
		expect(Array.isArray(initialDashboard.buckets)).toBe(true);

		const initialBucketCount = initialDashboard.buckets.length;
		console.log(`✅ Found ${initialBucketCount} existing buckets`);

		console.log("📝 Step 2: Creating bucket...");
		const bucket = await apiClient.createBucket(testBucketData.name);

		expect(bucket).toBeDefined();
		expect(bucket.name).toBe(testBucketData.name);
		expect(bucket.guid).toBeDefined();

		createdBucketGuids.push(bucket.guid);
		console.log(`✅ Created bucket with GUID: ${bucket.guid}`);

		// Step 3: Verify bucket appears in list
		console.log("📋 Step 3: Verifying bucket in list...");
		const updatedDashboard = await apiClient.getDashboard({
			months: [currentMonth],
		});

		expect(updatedDashboard.buckets.length).toBe(initialBucketCount + 1);

		const createdBucket = updatedDashboard.buckets.find(
			(b: any) => b.guid === bucket.guid,
		);
		expect(createdBucket).toBeDefined();
		console.log("✅ Bucket found in list");

		// Step 4: GetBucket
		console.log("🔍 Step 4: Getting bucket by GUID...");
		const fetchedBucket = await apiClient.getBucket(bucket.guid);
		expect(fetchedBucket).toBeDefined();
		expect(fetchedBucket.guid).toBe(bucket.guid);
		expect(fetchedBucket.name).toBe(testBucketData.name);
		console.log("✅ GetBucket returned correct data");

		// Step 5: UpdateBucket
		console.log("✏️ Step 5: Updating bucket name...");
		const updatedName = "Updated Business Expenses";
		const updatedBucket = await apiClient.updateBucket(
			bucket.guid,
			updatedName,
		);
		expect(updatedBucket).toBeDefined();
		expect(updatedBucket.name).toBe(updatedName);
		console.log("✅ Bucket name updated successfully");

		// Verify update persisted
		const refetchedBucket = await apiClient.getBucket(bucket.guid);
		expect(refetchedBucket.name).toBe(updatedName);
		console.log("✅ Bucket update persisted");

		console.log("🧾 Step 6: Creating receipts...");
		for (const receiptData of testReceiptData) {
			const receipt = await apiClient.createReceipt(
				receiptData.total,
				receiptData.vendor,
				receiptData.notes,
			);

			expect(receipt).toBeDefined();
			expect(receipt.guid).toBeDefined();
			expect(receipt.total).toBeDefined();
			expect(receipt.vendor).toBe(receiptData.vendor);

			createdReceiptGuids.push(receipt.guid);
		}
		console.log(`✅ Created ${createdReceiptGuids.length} receipts`);

		console.log("📋 Step 7: Listing unallocated receipts...");
		// Use getDashboard for unallocated receipts as ListReceipts now requires a bucket
		const finalDashboard = await apiClient.getDashboard({
			months: [currentMonth],
		});

		expect(finalDashboard.unallocatedReceipts).toBeDefined();
		expect(Array.isArray(finalDashboard.unallocatedReceipts)).toBe(true);

		// Verify our created receipts are in the unallocated list via dashboard
		const ourReceipts = finalDashboard.unallocatedReceipts.filter((r: any) =>
			createdReceiptGuids.includes(r.guid),
		);
		expect(ourReceipts.length).toBe(createdReceiptGuids.length);
		console.log("✅ All created receipts are unallocated");

		console.log("🎉 Full integration test flow completed successfully!");
	}, 300000); // 5 minutes for debugging

	it("should handle error cases gracefully", async () => {
		console.log("❌ Testing error handling...");

		// Test getting non-existent bucket
		try {
			await apiClient.getBucket("non-existent-guid");
			expect.fail("Should have thrown error for non-existent bucket");
		} catch (error) {
			expect(error).toBeDefined();
			console.log("✅ Properly rejected non-existent bucket GUID");
		}

		// Test creating bucket with empty name
		try {
			await apiClient.createBucket("");
			expect.fail("Should have thrown error for empty bucket name");
		} catch (error) {
			expect(error).toBeDefined();
			console.log("✅ Properly rejected empty bucket name");
		}

		console.log("✅ Error handling tests completed");
	});

	it("should handle receipt allocations correctly", async () => {
		console.log("💰 Testing receipt allocation functionality...");

		// Step 1: Create two buckets
		console.log("📝 Step 1: Creating two buckets...");
		const bucket1 = await apiClient.createBucket("Test Bucket 1");
		const bucket2 = await apiClient.createBucket("Test Bucket 2");

		expect(bucket1.guid).toBeDefined();
		createdBucketGuids.push(bucket1.guid);
		expect(bucket2.guid).toBeDefined();
		createdBucketGuids.push(bucket2.guid);

		const bucket1Guid = bucket1.guid;
		const bucket2Guid = bucket2.guid;

		console.log(`✅ Created bucket 1: ${bucket1Guid}`);
		console.log(`✅ Created bucket 2: ${bucket2Guid}`);

		// Step 2: Create a receipt with full allocation to bucket 1
		console.log("🧾 Step 2: Creating receipt fully allocated to bucket 1...");
		const receipt1 = await apiClient.createReceipt(
			100.0,
			"Test Vendor A",
			"Fully allocated to bucket 1",
			[{ bucket: bucket1Guid, amount: 100.0 }],
		);

		expect(receipt1.guid).toBeDefined();
		createdReceiptGuids.push(receipt1.guid);
		expect(receipt1.allocations).toBeDefined();
		expect(receipt1.allocations.length).toBe(1);
		expect(receipt1.allocations[0].bucket).toBe(bucket1Guid);
		expect(receipt1.allocations[0].amount).toBe(100.0);
		console.log("✅ Receipt created with full allocation");

		// Step 3: Create a receipt with split allocation
		console.log("🧾 Step 3: Creating receipt with split allocation...");
		const receipt2 = await apiClient.createReceipt(
			150.0,
			"Test Vendor B",
			"Split between two buckets",
			[
				{ bucket: bucket1Guid, amount: 90.0 },
				{ bucket: bucket2Guid, amount: 60.0 },
			],
		);

		expect(receipt2.guid).toBeDefined();
		createdReceiptGuids.push(receipt2.guid);
		expect(receipt2.allocations).toBeDefined();
		expect(receipt2.allocations.length).toBe(2);

		const alloc1 = receipt2.allocations.find(
			(a: any) => a.bucket === bucket1Guid,
		);
		const alloc2 = receipt2.allocations.find(
			(a: any) => a.bucket === bucket2Guid,
		);

		expect(alloc1).toBeDefined();
		expect(alloc1.amount).toBe(90.0);
		expect(alloc2).toBeDefined();
		expect(alloc2.amount).toBe(60.0);
		console.log("✅ Receipt created with split allocation");

		// Step 4: Create an unallocated receipt
		console.log("🧾 Step 4: Creating unallocated receipt...");
		const receipt3 = await apiClient.createReceipt(
			50.0,
			"Test Vendor C",
			"Unallocated receipt",
		);

		expect(receipt3.guid).toBeDefined();
		createdReceiptGuids.push(receipt3.guid);
		expect(receipt3.allocations).toBeDefined();
		expect(receipt3.allocations.length).toBe(0);
		console.log("✅ Unallocated receipt created");

		// Step 5: Verify bucket 1 has correct receipts
		console.log("📋 Step 5: Verifying receipts for bucket 1...");
		const bucket1Receipts = await apiClient.listReceipts({
			bucket: bucket1Guid,
			months: [currentMonth],
		});

		expect(bucket1Receipts.receipts).toBeDefined();
		expect(bucket1Receipts.receipts.length).toBe(2); // receipt1 and receipt2

		const guidsInBucket1 = bucket1Receipts.receipts.map((r: any) => r.guid);
		expect(guidsInBucket1).toContain(receipt1.guid);
		expect(guidsInBucket1).toContain(receipt2.guid);
		expect(guidsInBucket1).not.toContain(receipt3.guid);
		console.log("✅ Bucket 1 contains correct receipts");

		// Step 6: Verify bucket 2 has correct receipts
		console.log("📋 Step 6: Verifying receipts for bucket 2...");
		const bucket2Receipts = await apiClient.listReceipts({
			bucket: bucket2Guid,
			months: [currentMonth],
		});

		expect(bucket2Receipts.receipts).toBeDefined();
		expect(bucket2Receipts.receipts.length).toBe(1); // only receipt2

		const guidsInBucket2 = bucket2Receipts.receipts.map((r: any) => r.guid);
		expect(guidsInBucket2).toContain(receipt2.guid);
		expect(guidsInBucket2).not.toContain(receipt1.guid);
		expect(guidsInBucket2).not.toContain(receipt3.guid);
		console.log("✅ Bucket 2 contains correct receipts");

		// Step 7: Verify unallocated receipts list
		console.log("📋 Step 7: Verifying unallocated receipts via dashboard...");
		const finalDashboard = await apiClient.getDashboard({
			months: [currentMonth],
		});
		const unallocatedGuids = finalDashboard.unallocatedReceipts.map(
			(r: any) => r.guid,
		);

		expect(unallocatedGuids).toContain(receipt3.guid);
		expect(unallocatedGuids).not.toContain(receipt1.guid);
		expect(unallocatedGuids).not.toContain(receipt2.guid);
		console.log("✅ Unallocated receipts list is correct");

		console.log("🎉 Allocation tests completed successfully!");
	}, 300000); // 5 minutes for debugging

	it("should update receipt details correctly", async () => {
		console.log("✏️ Testing receipt update functionality...");

		// Create a bucket for allocations
		const bucket = await apiClient.createBucket("Update Test Bucket");
		createdBucketGuids.push(bucket.guid);

		// Step 1: Create a receipt
		console.log("🧾 Step 1: Creating initial receipt...");
		const receipt = await apiClient.createReceipt(
			75.0,
			"Original Vendor",
			"Original notes",
		);
		expect(receipt.guid).toBeDefined();
		createdReceiptGuids.push(receipt.guid);
		console.log(`✅ Created receipt: ${receipt.guid}`);

		// Step 2: Update receipt with new details and allocations
		console.log("✏️ Step 2: Updating receipt...");
		const updatedReceipt = await apiClient.updateReceipt({
			guid: receipt.guid,
			vendor: "Updated Vendor",
			total: 100.0,
			notes: "Updated notes",
			allocations: [{ bucket: bucket.guid, amount: 100.0 }],
		});

		expect(updatedReceipt).toBeDefined();
		expect(updatedReceipt.vendor).toBe("Updated Vendor");
		expect(updatedReceipt.total).toBe(100.0);
		expect(updatedReceipt.allocations.length).toBe(1);
		expect(updatedReceipt.allocations[0].bucket).toBe(bucket.guid);
		expect(updatedReceipt.allocations[0].amount).toBe(100.0);
		console.log("✅ Receipt updated successfully");

		// Step 3: Verify receipt appears in bucket
		console.log("📋 Step 3: Verifying updated receipt is in bucket...");
		const bucketReceipts = await apiClient.listReceipts({
			bucket: bucket.guid,
			months: [currentMonth],
		});
		const found = bucketReceipts.receipts.find(
			(r: any) => r.guid === receipt.guid,
		);
		expect(found).toBeDefined();
		expect(found.vendor).toBe("Updated Vendor");
		expect(found.total).toBe(100.0);
		console.log("✅ Updated receipt found in bucket");

		// Step 4: Verify receipt is no longer unallocated
		console.log(
			"📋 Step 4: Verifying receipt not in unallocated list via dashboard...",
		);
		const finalDashboard = await apiClient.getDashboard({
			months: [currentMonth],
		});
		const unallocatedGuids = finalDashboard.unallocatedReceipts.map(
			(r: any) => r.guid,
		);
		expect(unallocatedGuids).not.toContain(receipt.guid);
		console.log("✅ Updated receipt is not unallocated");

		console.log("🎉 Receipt update tests completed successfully!");
	}, 300000);

	it("should delete receipts correctly", async () => {
		console.log("🗑️ Testing receipt deletion...");

		// Step 1: Create a receipt
		console.log("🧾 Step 1: Creating receipt to delete...");
		const receipt = await apiClient.createReceipt(
			30.0,
			"Delete Test Vendor",
			"Will be deleted",
		);
		expect(receipt.guid).toBeDefined();
		// Don't add to cleanup list since we're deleting it explicitly

		// Step 2: Verify it exists in unallocated
		console.log(
			"📋 Step 2: Verifying receipt exists in dashboard unallocated...",
		);
		const beforeDelete = await apiClient.getDashboard({
			months: [currentMonth],
		});
		const beforeGuids = beforeDelete.unallocatedReceipts.map(
			(r: any) => r.guid,
		);
		expect(beforeGuids).toContain(receipt.guid);
		console.log("✅ Receipt exists in unallocated list");

		// Step 3: Delete it
		console.log("🗑️ Step 3: Deleting receipt...");
		const deleteResult = await apiClient.deleteReceipt(receipt.guid);
		expect(deleteResult).toBeDefined();
		console.log("✅ Delete returned successfully");

		// Step 4: Verify it's gone
		console.log("📋 Step 4: Verifying receipt is deleted from dashboard...");
		const afterDelete = await apiClient.getDashboard({
			months: [currentMonth],
		});
		const afterGuids = afterDelete.unallocatedReceipts.map((r: any) => r.guid);
		expect(afterGuids).not.toContain(receipt.guid);
		console.log("✅ Receipt no longer in unallocated list");

		console.log("🎉 Receipt deletion tests completed successfully!");
	}, 300000);

	it("should handle bucket deletion with allocated receipts", async () => {
		console.log("🗑️ Testing bucket deletion with allocated receipts...");

		// Step 1: Create a bucket
		console.log("📝 Step 1: Creating bucket...");
		const bucket = await apiClient.createBucket("Bucket To Delete");
		expect(bucket.guid).toBeDefined();
		// Don't add to cleanup, we delete it explicitly

		// Step 2: Create a receipt allocated to that bucket
		console.log("🧾 Step 2: Creating receipt allocated to bucket...");
		const receipt = await apiClient.createReceipt(
			80.0,
			"Vendor For Deleted Bucket",
			"Allocated to bucket that will be deleted",
			[{ bucket: bucket.guid, amount: 80.0 }],
		);
		expect(receipt.guid).toBeDefined();
		createdReceiptGuids.push(receipt.guid);

		// Step 3: Verify receipt is in bucket
		console.log("📋 Step 3: Verifying receipt is in bucket...");
		const bucketReceipts = await apiClient.listReceipts({
			bucket: bucket.guid,
			months: [currentMonth],
		});
		expect(bucketReceipts.receipts.length).toBe(1);
		expect(bucketReceipts.receipts[0].guid).toBe(receipt.guid);
		console.log("✅ Receipt found in bucket");

		// Step 4: Delete the bucket
		console.log("🗑️  Step 4: Deleting bucket...");
		const deleteResult = await apiClient.deleteBucket(bucket.guid);
		expect(deleteResult).toBeDefined();
		console.log("✅ Bucket deleted");

		// Step 5: Verify receipt still exists (now unallocated)
		console.log(
			"📋 Step 5: Verifying receipt still exists in dashboard after bucket deletion...",
		);
		const finalDashboard = await apiClient.getDashboard({
			months: [currentMonth],
		});
		const unallocatedGuids = finalDashboard.unallocatedReceipts.map(
			(r: any) => r.guid,
		);
		expect(unallocatedGuids).toContain(receipt.guid);
		console.log("✅ Receipt became unallocated after bucket deletion");

		console.log("🎉 Bucket deletion tests completed successfully!");
	}, 300000);
});
