import { test, expect } from "../fixtures";
import { addReceipt, openApp, switchToYear } from "./helpers";

test.describe("Vendor Management Flow", () => {
	test("open vendor card and view vendor detail", async ({
		page,
		tenant: _tenant,
	}) => {
		await openApp(page);

		// Create a receipt to register a vendor
		await addReceipt(page, { vendor: "Acme Corp", total: "25.00" });
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
		await openApp(page);

		// Create a receipt to register a vendor
		await addReceipt(page, { vendor: "ValidVendor", total: "10.00" });
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

	test("empty vendor stays hidden in an empty year until show empty is enabled", async ({
		page,
		tenant: _tenant,
	}) => {
		const nextYear = String(new Date().getFullYear() + 1);

		await openApp(page);
		await addReceipt(page, { vendor: "Year Switch Vendor", total: "18.25" });

		await expect(
			page.locator(".card", { has: page.getByText("Unallocated") }),
		).toContainText("$18.25");

		await page.getByRole("button", { name: "Vendors" }).click();
		await expect(
			page.getByRole("heading", { level: 2, name: "Vendors" }),
		).toBeVisible();

		await expect(
			page.locator(".card").filter({ hasText: "Year Switch Vendor" }),
		).toBeVisible();

		await switchToYear(page, nextYear);

		const vendorCard = page
			.locator(".card")
			.filter({ has: page.getByText("Year Switch Vendor") });
		await expect(vendorCard).not.toBeVisible();

		await page.getByRole("button", { name: "Show Empty" }).click();

		await expect(vendorCard).toBeVisible();
		await expect(vendorCard).toContainText("$0.00");
		await expect(vendorCard).toContainText("(0)");
	});

	test("rename a vendor from the vendor detail page", async ({
		page,
		tenant: _tenant,
	}) => {
		await openApp(page);
		await addReceipt(page, { vendor: "Old Vendor", total: "33.40" });

		await expect(
			page.locator(".card", { has: page.getByText("Unallocated") }),
		).toContainText("$33.40");

		await page.getByRole("button", { name: "Vendors" }).click();
		await expect(
			page.getByRole("heading", { level: 2, name: "Vendors" }),
		).toBeVisible();

		await page.locator(".card").filter({ hasText: "Old Vendor" }).click();
		await expect(
			page.getByRole("heading", { level: 2, name: "Old Vendor" }),
		).toBeVisible();

		await page.getByRole("heading", { level: 2, name: "Old Vendor" }).hover();
		await page.getByTitle("Rename Vendor").click();

		const renameInput = page.getByRole("textbox");
		await expect(renameInput).toBeVisible();
		await renameInput.fill("Renamed Vendor");
		await page.keyboard.press("Enter");

		await expect(
			page.getByRole("heading", { level: 2, name: "Renamed Vendor" }),
		).toBeVisible();

		// Navigate back using the in-detail back arrow (inside the main content)
		await page.locator("main").getByRole("button").first().click();

		await expect(
			page.locator(".card").filter({ has: page.getByText("Renamed Vendor") }),
		).toBeVisible();
	});
});
