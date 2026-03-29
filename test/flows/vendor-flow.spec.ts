import { test, expect } from "../fixtures";

test.describe("Vendor Management Flow", () => {
	test("open vendor card and view vendor detail", async ({
		page,
		tenant: _tenant,
	}) => {
		await page.goto("/");
		await expect(page.getByText("TAXOS")).toBeVisible();

		// Create a receipt to register a vendor
		await page.getByRole("button", { name: "Add Receipt" }).click();
		const modal = page.locator(".modal-overlay");
		await expect(modal).toBeVisible();
		await modal.getByPlaceholder("e.g. Amazon").fill("Acme Corp");
		await modal
			.locator('input[type="number"][placeholder="0.00"]')
			.fill("25.00");
		await modal.getByRole("button", { name: "Save Receipt" }).click();
		await expect(modal).not.toBeVisible();
		// Wait for the receipt to be saved and dashboard to reflect it before
		// navigating away; ensures the vendor exists on the server.
		await expect(
			page.locator(".card", { has: page.getByText("Unallocated") }),
		).toContainText("$25.00");

		// Navigate to the Vendors view
		await page.getByRole("button", { name: "Vendors" }).click();
		await expect(
			page.getByRole("heading", { level: 2, name: "Vendors" }),
		).toBeVisible();

		// Shared header remains visible in every view
		await expect(page.getByText("Receipts")).toBeVisible();

		const vendorCard = page.locator(".card").filter({ hasText: "Acme Corp" });
		await expect(vendorCard).toBeVisible();

		// Click through to vendor detail and verify receipt list view appears.
		await vendorCard.click();
		await expect(
			page.getByRole("heading", { level: 2, name: "Acme Corp" }),
		).toBeVisible();
		await expect(page.getByText("$25.00").first()).toBeVisible();
	});

	test("vendors view keeps date and action controls", async ({
		page,
		tenant: _tenant,
	}) => {
		await page.goto("/");
		await expect(page.getByText("TAXOS")).toBeVisible();

		// Create a receipt to register a vendor
		await page.getByRole("button", { name: "Add Receipt" }).click();
		const modal = page.locator(".modal-overlay");
		await expect(modal).toBeVisible();
		await modal.getByPlaceholder("e.g. Amazon").fill("ValidVendor");
		await modal
			.locator('input[type="number"][placeholder="0.00"]')
			.fill("10.00");
		await modal.getByRole("button", { name: "Save Receipt" }).click();
		await expect(modal).not.toBeVisible();
		// Wait for dashboard to confirm receipt saved
		await expect(
			page.locator(".card", { has: page.getByText("Unallocated") }),
		).toContainText("$10.00");

		// Navigate to Vendors
		await page.getByRole("button", { name: "Vendors" }).click();
		await expect(
			page.getByRole("heading", { level: 2, name: "Vendors" }),
		).toBeVisible();

		// Top bar controls are preserved in vendors view.
		await expect(page.getByRole("button", { name: "Year" })).toBeVisible();
		await expect(page.getByRole("button", { name: "Month" })).toBeVisible();
		await expect(
			page.getByRole("button", { name: "Add Receipt" }),
		).toBeVisible();
		await expect(
			page.getByRole("button", { name: "Upload File" }),
		).toBeVisible();

		// Vendor card should be present in vendors mode.
		await expect(
			page.locator(".card").filter({ hasText: "ValidVendor" }),
		).toBeVisible();
	});
});
