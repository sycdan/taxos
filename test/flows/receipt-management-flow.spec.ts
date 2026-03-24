import { test, expect } from "../fixtures";
import type { Page } from "@playwright/test";

async function createBucket(page: Page, name: string) {
	await page.getByRole("button", { name: "Add Bucket" }).click();
	await page.getByPlaceholder("e.g. Travel, Office Supplies").fill(name);
	await page.getByRole("button", { name: "Create Bucket" }).click();
	// Wait for the form to close AND for the bucket to appear in the sidebar
	// click-through button (Show Empty) so we know state has settled.
	await expect(
		page.getByPlaceholder("e.g. Travel, Office Supplies"),
	).not.toBeVisible();
}

async function addReceipt(
	page: Page,
	options: { vendor: string; total: string; buckets?: string[] },
) {
	await page.getByRole("button", { name: "Add Receipt" }).click();
	const modal = page.locator(".modal-overlay");
	await expect(modal).toBeVisible();
	await modal.getByPlaceholder("e.g. Amazon").fill(options.vendor);
	await modal
		.locator('input[type="number"][placeholder="0.00"]')
		.fill(options.total);
	for (const bucketName of options.buckets ?? []) {
		// Wait for the chip to appear (it depends on the bucketSummaries context
		// state settling after the async bucket creation).
		const chip = modal.locator(".chip", { hasText: bucketName });
		await expect(chip).toBeVisible({ timeout: 15_000 });
		await chip.click();
	}
	await modal.getByRole("button", { name: "Save Receipt" }).click();
	await expect(modal).not.toBeVisible();
}

test.describe("Receipt Management Flow", () => {
	test("view, edit, and delete a receipt from bucket detail", async ({
		page,
		tenant: _tenant,
	}) => {
		await page.goto("/");
		await expect(page.getByText("TAXOS")).toBeVisible();

		// Create a bucket and add an allocated receipt
		await createBucket(page, "Travel");
		await addReceipt(page, {
			vendor: "Uber",
			total: "45.00",
			buckets: ["Travel"],
		});

		// Bucket card shows the correct total
		const travelCard = page.locator(".card", { has: page.getByText("Travel") });
		await expect(travelCard).toContainText("$45.00");

		// Navigate to bucket detail
		await travelCard.click();
		await expect(page.getByRole("heading", { name: "Travel" })).toBeVisible();

		// Receipt row is visible
		const receiptRow = page.locator(".card", { has: page.getByText("Uber") });
		await expect(receiptRow).toBeVisible();

		// ── Edit: change vendor name ───────────────────────────────────────────
		await receiptRow.click();
		const modal = page.locator(".modal-overlay");
		await expect(modal).toBeVisible();
		await expect(
			modal.getByRole("heading", { name: "Edit Receipt" }),
		).toBeVisible();

		await modal.getByPlaceholder("e.g. Amazon").fill("Uber Eats");
		await modal.getByRole("button", { name: "Save Receipt" }).click();
		await expect(modal).not.toBeVisible();

		// Updated vendor name now appears
		await expect(
			page.locator(".card", { has: page.getByText("Uber Eats") }),
		).toBeVisible();

		// ── Delete the receipt ────────────────────────────────────────────────
		await page.locator(".card", { has: page.getByText("Uber Eats") }).click();
		await expect(modal).toBeVisible();
		page.once("dialog", (dialog) => dialog.accept());
		await modal.getByRole("button", { name: "Delete Receipt" }).click();

		// Bucket detail shows empty state
		await expect(
			page.getByText("No receipts found for this period."),
		).toBeVisible();
	});

	test("unallocated receipt can be reallocated to a bucket", async ({
		page,
		tenant: _tenant,
	}) => {
		await page.goto("/");
		await expect(page.getByText("TAXOS")).toBeVisible();

		// Create a bucket, then add a receipt with no allocation
		await createBucket(page, "Entertainment");
		await addReceipt(page, { vendor: "Netflix", total: "15.00" });

		// Receipt appears in Unallocated
		const unallocatedCard = page.locator(".card", {
			has: page.getByText("Unallocated"),
		});
		await expect(unallocatedCard).toContainText("$15.00");

		// Navigate to Unallocated detail and confirm receipt is there
		await unallocatedCard.click();
		const receiptRow = page.locator(".card", {
			has: page.getByText("Netflix"),
		});
		await expect(receiptRow).toBeVisible();

		// Edit receipt: add allocation to "Entertainment"
		await receiptRow.click();
		const modal = page.locator(".modal-overlay");
		await expect(modal).toBeVisible();
		await modal.locator(".chip", { hasText: "Entertainment" }).click();
		await modal.getByRole("button", { name: "Save Receipt" }).click();
		await expect(modal).not.toBeVisible();

		// Back to dashboard: Entertainment bucket now shows $15.00
		await page.getByRole("button", { name: "Back to Dashboard" }).click();
		const entertainmentCard = page.locator(".card", {
			has: page.getByText("Entertainment"),
		});
		await expect(entertainmentCard).toContainText("$15.00");
	});

	test("receipt is split automatically across two buckets", async ({
		page,
		tenant: _tenant,
	}) => {
		await page.goto("/");
		await expect(page.getByText("TAXOS")).toBeVisible();

		await createBucket(page, "Food");
		await createBucket(page, "Work");

		// Create receipt and add both buckets — auto-split distributes evenly
		await page.getByRole("button", { name: "Add Receipt" }).click();
		const modal = page.locator(".modal-overlay");
		await expect(modal).toBeVisible();
		await modal.getByPlaceholder("e.g. Amazon").fill("Costco");
		await modal
			.locator('input[type="number"][placeholder="0.00"]')
			.fill("100.00");
		await modal.locator(".chip", { hasText: "Food" }).click();
		await modal.locator(".chip", { hasText: "Work" }).click();
		await modal.getByRole("button", { name: "Save Receipt" }).click();
		await expect(modal).not.toBeVisible();

		// Both buckets should each show $50.00
		await expect(
			page.locator(".card", { has: page.getByText("Food") }),
		).toContainText("$50.00");
		await expect(
			page.locator(".card", { has: page.getByText("Work") }),
		).toContainText("$50.00");
	});

	test("rename a bucket via bucket detail, then delete it — receipts become unallocated", async ({
		page,
		tenant: _tenant,
	}) => {
		await page.goto("/");
		await expect(page.getByText("TAXOS")).toBeVisible();

		await createBucket(page, "OldBucket");

		// Add a receipt to the bucket so it is visible without "Show Empty"
		await addReceipt(page, {
			vendor: "Target",
			total: "80.00",
			buckets: ["OldBucket"],
		});

		// Navigate to bucket detail
		await page.locator(".card", { has: page.getByText("OldBucket") }).click();
		await expect(
			page.getByRole("heading", { name: "OldBucket" }),
		).toBeVisible();

		// ── Rename bucket ─────────────────────────────────────────────────────
		await page.getByRole("heading", { name: "OldBucket" }).hover();
		await page.getByTitle("Rename Bucket").click();
		// Scope to <main> to avoid matching the month filter input in <header>
		const renameInput = page.getByRole("main").getByRole("textbox");
		await expect(renameInput).toBeVisible();
		await renameInput.fill("RenamedBucket");
		await page.keyboard.press("Enter");
		await expect(
			page.getByRole("heading", { name: "RenamedBucket" }),
		).toBeVisible();

		// ── Delete bucket ─────────────────────────────────────────────────────
		await page.getByRole("heading", { name: "RenamedBucket" }).hover();
		page.once("dialog", (dialog) => dialog.accept());
		await page.getByTitle("Delete Bucket").click();

		// App navigates back to dashboard automatically
		await expect(
			page.getByRole("button", { name: "Add Bucket" }),
		).toBeVisible();

		// Deleted bucket is gone from dashboard
		await expect(
			page.locator(".card", { has: page.getByText("RenamedBucket") }),
		).not.toBeVisible();

		// Receipt is now unallocated — Unallocated card shows $80.00
		await expect(
			page.locator(".card", { has: page.getByText("Unallocated") }),
		).toContainText("$80.00");
	});
});
