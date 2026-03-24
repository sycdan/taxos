import { test, expect } from "../fixtures";

test.describe("Backdated Receipt Flow", () => {
	test("backdated receipt appears in the correct month on the dashboard", async ({
		page,
		tenant: _tenant,
	}) => {
		const today = new Date();
		const currentYear = today.getFullYear();
		const currentMonth = `${currentYear}-${String(today.getMonth() + 1).padStart(2, "0")}`;

		// Use mid-year (June) of the prior year as the backdated date.
		const priorYear = currentYear - 1;
		const backdatedMonth = `${priorYear}-06`;
		const backdatedDatetime = `${priorYear}-06-15T12:00`;
		const bucketName = "Backdated Test Bucket";
		const bucketNameRegex = new RegExp(bucketName, "i");
		const receiptTotal = "75.50";

		// ── 1. Load the app ──────────────────────────────────────────────────────
		await page.goto("/");
		await expect(page.getByText("TAXOS")).toBeVisible();

		// ── 2. Create a bucket via the dashboard UI ──────────────────────────────
		await page.getByRole("button", { name: "Add Bucket" }).click();
		await page
			.getByPlaceholder("e.g. Travel, Office Supplies")
			.fill(bucketName);
		await page.getByRole("button", { name: "Create Bucket" }).click();

		// ── 3. Verify the filter is in month mode at the current month ──────────
		const monthInput = page.locator('input[type="month"]');
		await expect(monthInput).toBeVisible();
		await expect(monthInput).toHaveValue(currentMonth);

		// The Month mode button should carry the "active" class.
		await expect(page.getByRole("button", { name: /^Month$/i })).toHaveClass(
			/active/,
		);

		// ── 4. Verify the bucket is hidden (empty buckets are hidden by default) ──
		const bucketCard = page.locator(".card", {
			has: page.getByText(bucketNameRegex),
		});
		await expect(bucketCard).not.toBeVisible();

		// ── 5. Add a backdated receipt allocated to the bucket ───────────────────
		await page.getByRole("button", { name: "Add Receipt" }).click();

		const modal = page.locator(".modal-overlay");
		await expect(modal).toBeVisible();

		// Fill in vendor name
		await modal.getByPlaceholder("e.g. Amazon").fill("Backdated Vendor");

		// Fill in amount
		await modal
			.locator('input[type="number"][placeholder="0.00"]')
			.fill(receiptTotal);

		// Fill in the backdated timestamp
		await modal.locator('input[type="datetime-local"]').fill(backdatedDatetime);

		// Allocate to the bucket via the chip — wait for it to appear first since
		// bucketSummaries state may still be settling after bucket creation.
		const bucketChip = modal.getByRole("button", { name: bucketNameRegex });
		await expect(bucketChip).toBeVisible({ timeout: 15_000 });
		await bucketChip.click();

		// Save the receipt and close the modal
		await modal.getByRole("button", { name: "Save Receipt" }).click();
		await expect(modal).not.toBeVisible();

		// ── 6. Ensure app auto-switches to the backdated month ───────────────────
		// After saving a new receipt the app updates the filter to match the
		// receipt's date — no manual filter change needed.
		await expect(monthInput).toHaveValue(backdatedMonth);

		const backdatedCard = page.locator(".card", {
			has: page.getByText(bucketNameRegex),
		});
		await expect(backdatedCard).toBeVisible();
		await expect(backdatedCard.getByText(`$${receiptTotal}`)).toBeVisible();

		// ── 7. Switch back to current month — bucket is hidden again (empty) ─────
		await monthInput.fill(currentMonth);
		await monthInput.dispatchEvent("change");

		// Empty bucket should not appear since we did not click "Show Empty"
		await expect(
			page.locator(".card", { has: page.getByText(bucketNameRegex) }),
		).not.toBeVisible();
	});
});
