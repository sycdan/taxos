import { test, expect } from "../fixtures";

test.describe("Vendor Management Flow", () => {
	test("rename a vendor from the Vendors page", async ({
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

		// Navigate to the Vendors page
		await page.getByRole("button", { name: "Vendors" }).click();
		await expect(
			page.getByRole("heading", { level: 1, name: "Vendors" }),
		).toBeVisible();

		// Find the vendor card — use .filter({ hasText }) which matches the
		// card's textContent in normal (non-editing) display mode.
		const vendorCard = page.locator(".card").filter({ hasText: "Acme Corp" });
		await expect(vendorCard).toBeVisible();
		await vendorCard.getByTitle("Rename vendor").click();

		// Edit the name and confirm. The card filter (hasText) stops matching once
		// the vendor name is replaced by an input, so query page-wide instead.
		// The month filter is hidden on the Vendors page so this is unambiguous.
		const nameInput = page.getByRole("textbox");
		await expect(nameInput).toBeVisible();
		await nameInput.fill("Acme Ltd");
		await page.keyboard.press("Enter");

		// New name visible, old name gone
		await expect(page.getByText("Acme Ltd")).toBeVisible();
		await expect(page.getByText("Acme Corp")).not.toBeVisible();
	});

	test("save button is disabled when vendor name is cleared", async ({
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

		// Open the inline edit form
		const vendorCard = page.locator(".card").filter({ hasText: "ValidVendor" });
		await expect(vendorCard).toBeVisible();
		await vendorCard.getByTitle("Rename vendor").click();

		// Clear the name field (same reasoning: filter no longer matches after edit mode)
		await page.getByRole("textbox").fill("");

		// The save (check) button must be disabled
		await expect(page.getByTitle("Save")).toBeDisabled();

		// Cancel to leave state clean
		await page.getByTitle("Cancel").click();
		await expect(page.getByText("ValidVendor")).toBeVisible();
	});
});
