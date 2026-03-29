import { test, expect } from "../fixtures";
import { addReceipt, createBucket, openApp, switchToMonth } from "./helpers";

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
		await openApp(page);

		// ── 2. Create a bucket via the dashboard UI ──────────────────────────────
		await createBucket(page, bucketName);

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
		await addReceipt(page, {
			vendor: "Backdated Vendor",
			total: receiptTotal,
			dateTime: backdatedDatetime,
			buckets: [bucketName],
		});

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
		await switchToMonth(page, currentMonth);

		// Empty bucket should not appear since we did not click "Show Empty"
		await expect(
			page.locator(".card", { has: page.getByText(bucketNameRegex) }),
		).not.toBeVisible();
	});
});
