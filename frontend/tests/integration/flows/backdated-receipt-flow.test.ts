import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { createTestClient } from "../../utils/api-client";

describe("Backdated Receipt Flow", () => {
	const apiClient = createTestClient();
	let createdBucketGuids: string[] = [];
	let createdReceiptGuids: string[] = [];

	beforeEach(() => {
		createdBucketGuids = [];
		createdReceiptGuids = [];
	});

	afterEach(async () => {
		for (const guid of createdReceiptGuids) {
			try {
				await apiClient.deleteReceipt(guid);
			} catch {
				console.warn(`⚠️ Failed to clean up receipt ${guid}`);
			}
		}
		if (createdReceiptGuids.length > 0) {
			console.log(`✅ Cleaned up ${createdReceiptGuids.length} receipts`);
		}

		for (const guid of createdBucketGuids) {
			try {
				await apiClient.deleteBucket(guid);
			} catch {
				console.warn(`⚠️ Failed to clean up bucket ${guid}`);
			}
		}
		if (createdBucketGuids.length > 0) {
			console.log(`✅ Cleaned up ${createdBucketGuids.length} buckets`);
		}
	});

	it("should show a backdated receipt in the correct month on the dashboard", async () => {
		console.log("📅 Testing backdated receipt flow...");

		// Derive date values
		const today = new Date();
		const currentYear = today.getFullYear();
		const currentMonth = `${currentYear}-${String(today.getMonth() + 1).padStart(2, "0")}`;

		// Middle of the prior year: June 15
		const priorYear = currentYear - 1;
		const backdatedDate = new Date(priorYear, 5, 15); // June 15 of last year
		const backdatedMonth = `${priorYear}-06`;

		console.log(`📆 Current filter month: ${currentMonth}`);
		console.log(`📆 Backdated receipt month: ${backdatedMonth}`);

		// Step 1: Create a bucket
		console.log("📝 Step 1: Creating bucket...");
		const bucket = await apiClient.createBucket(
			`Backdated Test Bucket ${Date.now()}`,
		);
		expect(bucket.guid).toBeDefined();
		createdBucketGuids.push(bucket.guid);
		console.log(`✅ Created bucket: ${bucket.guid}`);

		// Step 2: Confirm current-month dashboard does NOT yet show the bucket
		//         with any amount (totalAmount should be 0)
		console.log(
			"📋 Step 2: Confirming bucket has no receipts in current month...",
		);
		const dashboardBefore = await apiClient.getDashboard({
			months: [currentMonth],
		});
		const summaryBefore = dashboardBefore.buckets.find(
			(b) => b.guid === bucket.guid,
		);
		expect(summaryBefore).toBeDefined();
		expect(summaryBefore!.totalAmount).toBe(0);
		console.log("✅ Bucket shows $0 in current month (as expected)");

		// Step 3: Create a backdated receipt allocated to the bucket
		const receiptTotal = 75.5;
		console.log(
			`🧾 Step 3: Creating receipt for ${backdatedMonth} with total $${receiptTotal}...`,
		);
		const receipt = await apiClient.createReceipt(
			receiptTotal,
			"Backdated Vendor",
			"Backdated receipt test",
			[{ bucket: bucket.guid, amount: receiptTotal }],
			backdatedDate,
		);
		expect(receipt.guid).toBeDefined();
		createdReceiptGuids.push(receipt.guid);
		console.log(`✅ Created receipt: ${receipt.guid}`);

		// Step 4: Simulate the filter updating — query dashboard for the
		//         backdated month (mirrors what the UI does when filter changes)
		console.log(
			`📋 Step 4: Querying dashboard for backdated month (${backdatedMonth})...`,
		);
		const dashboardBackdated = await apiClient.getDashboard({
			months: [backdatedMonth],
		});
		const summaryBackdated = dashboardBackdated.buckets.find(
			(b) => b.guid === bucket.guid,
		);
		expect(summaryBackdated).toBeDefined();
		expect(summaryBackdated!.totalAmount).toBe(receiptTotal);
		expect(summaryBackdated!.receiptCount).toBe(1);
		console.log(
			`✅ Dashboard for ${backdatedMonth} shows $${summaryBackdated!.totalAmount} in bucket`,
		);

		// Step 5: Confirm the receipt does NOT appear in the current-month dashboard
		console.log(
			"📋 Step 5: Confirming receipt is absent from current-month dashboard...",
		);
		const dashboardCurrentAfter = await apiClient.getDashboard({
			months: [currentMonth],
		});
		const summaryCurrentAfter = dashboardCurrentAfter.buckets.find(
			(b) => b.guid === bucket.guid,
		);
		expect(summaryCurrentAfter).toBeDefined();
		expect(summaryCurrentAfter!.totalAmount).toBe(0);
		console.log(
			"✅ Backdated receipt correctly absent from current-month view",
		);

		// Step 6: Verify the receipt is listed under the bucket for that month
		console.log(
			`📋 Step 6: Listing receipts for bucket in ${backdatedMonth}...`,
		);
		const receiptsInMonth = await apiClient.listReceipts({
			bucket: bucket.guid,
			months: [backdatedMonth],
		});
		expect(receiptsInMonth.receipts.length).toBe(1);
		expect(receiptsInMonth.receipts[0].guid).toBe(receipt.guid);
		expect(receiptsInMonth.receipts[0].total).toBe(receiptTotal);
		console.log(`✅ Receipt found in bucket listing for ${backdatedMonth}`);

		console.log("🎉 Backdated receipt flow completed successfully!");
	}, 300000);
});
