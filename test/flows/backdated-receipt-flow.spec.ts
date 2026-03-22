import { test, expect } from "../fixtures";

test.describe("Backdated Receipt Flow", () => {
	test("backdated receipt appears in the correct month on the dashboard", async ({
		page,
		tenant: _tenant,
	}) => {
		const today = new Date();
		const currentYear = today.getFullYear();
		const currentMonth = `${currentYear}-${String(today.getMonth() + 1).padStart(2, "0")}`;
		const priorYear = currentYear - 1;
		// Use mid-year (June) of the prior year as the backdated date.
		const backdatedMonth = `${priorYear}-06`;
		const backdatedDatetime = `${priorYear}-06-15T12:00`;
		const bucketName = `Backdated Bucket ${Date.now()}`;
		const receiptTotal = "75.50";

		// ── 1. Load the app ──────────────────────────────────────────────────────
		// The tenant fixture already set taxos_token in localStorage via addInitScript,
		// so the app boots directly into the authenticated view.
		await page.goto("/");
		await expect(page.getByText("TAXOS")).toBeVisible();

		// Show empty buckets now so newly-created (empty) buckets are visible.
		await page.getByRole("button", { name: /Show Empty/i }).click();

		// ── 2. Create a bucket via the dashboard UI ──────────────────────────────
		await page.getByRole("button", { name: "Add Bucket" }).click();
		await page
			.getByPlaceholder("e.g. Travel, Office Supplies")
			.fill(bucketName);
		await page.getByRole("button", { name: "Create Bucket" }).click();

		// Bucket card appears on the dashboard (name rendered as uppercase label).
		// Use a case-insensitive regex to match regardless of CSS text-transform.
		await expect(
			page.getByText(new RegExp(bucketName, "i")).first(),
		).toBeVisible();

		// ── 3. Verify the bucket shows $0.00 in the current month ────────────────
		const bucketCard = page.locator(".card", {
			has: page.getByText(new RegExp(bucketName, "i")),
		});
		await expect(bucketCard).toBeVisible();
		await expect(bucketCard.getByText("$0.00")).toBeVisible();

		// ── 4. Switch the month filter to the backdated month ────────────────────
		await page.locator('input[type="month"]').fill(backdatedMonth);
		// Trigger change event — some browsers need explicit dispatch after programmatic fill.
		await page.locator('input[type="month"]').dispatchEvent("change");

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

		// Set the date to the backdated month
		await modal.locator('input[type="datetime-local"]').fill(backdatedDatetime);

		// Allocate to the bucket via the chip
		await modal
			.getByRole("button", { name: new RegExp(bucketName, "i") })
			.click();

		// Save
		await modal.getByRole("button", { name: "Save Receipt" }).click();
		await expect(modal).not.toBeVisible();

		// ── 6. Dashboard for the backdated month shows the correct total ─────────
		await expect(
			page.locator(".card", {
				has: page.getByText(new RegExp(bucketName, "i")),
			}),
		).toBeVisible();

		const backdatedCard = page.locator(".card", {
			has: page.getByText(new RegExp(bucketName, "i")),
		});
		await expect(backdatedCard.getByText(`$${receiptTotal}`)).toBeVisible();

		// ── 7. Switch back to current month — bucket should show $0.00 ──────────
		await page.locator('input[type="month"]').fill(currentMonth);
		await page.locator('input[type="month"]').dispatchEvent("change");

		// The bucket may be hidden when empty — it was already shown earlier.
		const currentCard = page.locator(".card", {
			has: page.getByText(new RegExp(bucketName, "i")),
		});
		await expect(currentCard).toBeVisible();
		await expect(currentCard.getByText("$0.00")).toBeVisible();
	});
});
