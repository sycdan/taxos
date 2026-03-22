import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { createTestClient } from "../../utils/api-client";

describe("Vendor Management Flow", () => {
	const apiClient = createTestClient();
	let createdReceiptGuids: string[] = [];
	const currentMonth = new Date().toISOString().slice(0, 7);

	beforeEach(async () => {
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
	});

	it("should list vendors and see newly created ones from receipts", async () => {
		console.log("🏷️  Testing vendor list...");

		const vendorName = `Test Vendor ${Date.now()}`;

		// Create a receipt which auto-creates a vendor
		console.log(`📝 Creating receipt for vendor: ${vendorName}`);
		const receipt = await apiClient.createReceipt(
			10.0,
			vendorName,
			"Vendor list test receipt",
		);
		expect(receipt.guid).toBeDefined();
		createdReceiptGuids.push(receipt.guid);
		console.log(`✅ Created receipt ${receipt.guid}`);

		// List vendors and verify new vendor appears
		console.log("📋 Listing vendors...");
		const response = await apiClient.listVendors();
		expect(response).toBeDefined();
		expect(Array.isArray(response.vendors)).toBe(true);

		const found = response.vendors.find((v) => v.name === vendorName);
		expect(found).toBeDefined();
		expect(found!.guid).toBeDefined();
		expect(found!.name).toBe(vendorName);
		console.log(`✅ Vendor "${vendorName}" found in list with GUID ${found!.guid}`);

		console.log("🎉 Vendor list test completed successfully!");
	}, 300000);

	it("should rename a vendor", async () => {
		console.log("✏️  Testing vendor rename...");

		const originalName = `Rename Test Vendor ${Date.now()}`;
		const updatedName = `${originalName} (renamed)`;

		// Create a receipt to get a vendor
		console.log(`📝 Creating receipt for vendor: ${originalName}`);
		const receipt = await apiClient.createReceipt(
			20.0,
			originalName,
			"Vendor rename test",
		);
		expect(receipt.guid).toBeDefined();
		createdReceiptGuids.push(receipt.guid);

		// Find the vendor GUID
		console.log("🔍 Finding vendor GUID...");
		const listResponse = await apiClient.listVendors();
		const vendor = listResponse.vendors.find((v) => v.name === originalName);
		expect(vendor).toBeDefined();
		const vendorGuid = vendor!.guid;
		console.log(`✅ Found vendor GUID: ${vendorGuid}`);

		// Rename the vendor
		console.log(`✏️  Renaming vendor to: ${updatedName}`);
		const updated = await apiClient.updateVendor(vendorGuid, updatedName);
		expect(updated).toBeDefined();
		expect(updated.guid).toBe(vendorGuid);
		expect(updated.name).toBe(updatedName);
		console.log(`✅ Vendor renamed to "${updated.name}"`);

		// Verify the rename persisted in list
		console.log("✅ Verifying rename persisted...");
		const afterRenameList = await apiClient.listVendors();
		const renamedVendor = afterRenameList.vendors.find(
			(v) => v.guid === vendorGuid,
		);
		expect(renamedVendor).toBeDefined();
		expect(renamedVendor!.name).toBe(updatedName);

		const oldName = afterRenameList.vendors.find((v) => v.name === originalName);
		expect(oldName).toBeUndefined();
		console.log("✅ Old vendor name no longer present");

		console.log("🎉 Vendor rename test completed successfully!");
	}, 300000);

	it("should return vendor list sorted by name", async () => {
		console.log("🔤 Testing vendor list sorting...");

		const timestamp = Date.now();
		const names = [
			`ZZZ Sort Test Vendor ${timestamp}`,
			`AAA Sort Test Vendor ${timestamp}`,
			`MMM Sort Test Vendor ${timestamp}`,
		];

		// Create receipts for each unique vendor
		for (const name of names) {
			const receipt = await apiClient.createReceipt(5.0, name, "Sort test");
			expect(receipt.guid).toBeDefined();
			createdReceiptGuids.push(receipt.guid);
		}
		console.log(`✅ Created ${names.length} vendor receipts`);

		// List and check sorting
		const response = await apiClient.listVendors();
		const ourVendors = response.vendors.filter((v) =>
			names.includes(v.name),
		);
		expect(ourVendors.length).toBe(3);

		// Verify sorted order (case-insensitive ascending)
		const sortedNames = ourVendors.map((v) => v.name);
		const expectedOrder = [...names].sort((a, b) =>
			a.toLowerCase().localeCompare(b.toLowerCase()),
		);
		expect(sortedNames).toEqual(expectedOrder);
		console.log(`✅ Vendors returned in sorted order: ${sortedNames.join(", ")}`);

		console.log("🎉 Sort test completed successfully!");
	}, 300000);

	it("should reject updating a vendor with an empty name", async () => {
		console.log("🚫 Testing invalid vendor update...");

		const vendorName = `Empty Name Test Vendor ${Date.now()}`;

		const receipt = await apiClient.createReceipt(
			15.0,
			vendorName,
			"Empty name test receipt",
		);
		createdReceiptGuids.push(receipt.guid);

		const listResponse = await apiClient.listVendors();
		const vendor = listResponse.vendors.find((v) => v.name === vendorName);
		expect(vendor).toBeDefined();

		// Try to update with empty name — should fail
		try {
			await apiClient.updateVendor(vendor!.guid, "");
			expect.fail("Should have rejected empty vendor name");
		} catch (error) {
			expect(error).toBeDefined();
			console.log("✅ Properly rejected empty vendor name");
		}

		// Verify name unchanged
		const afterList = await apiClient.listVendors();
		const unchanged = afterList.vendors.find((v) => v.guid === vendor!.guid);
		expect(unchanged).toBeDefined();
		expect(unchanged!.name).toBe(vendorName);
		console.log("✅ Vendor name unchanged after failed update");

		console.log("🎉 Invalid update test completed successfully!");
	}, 300000);
});
