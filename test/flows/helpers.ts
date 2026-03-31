import { expect, type Page } from "@playwright/test";

export async function openApp(page: Page) {
	await page.goto("/");
	await expect(page.getByText("TAXOS")).toBeVisible();
}

export async function createBucket(page: Page, name: string) {
	await page.getByRole("button", { name: "Add Bucket" }).click();
	await page.getByPlaceholder("e.g. Travel, Office Supplies").fill(name);
	await page.getByRole("button", { name: "Create Bucket" }).click();
	await expect(
		page.getByPlaceholder("e.g. Travel, Office Supplies"),
	).not.toBeVisible();
}

export async function addReceipt(
	page: Page,
	options: {
		vendor: string;
		total: string;
		buckets?: string[];
		dateTime?: string;
	},
) {
	await page.getByRole("button", { name: "Add Receipt" }).click();
	const modal = page.locator(".modal-overlay");
	await expect(modal).toBeVisible();
	await expect(
		modal.getByRole("heading", { name: "New Receipt" }),
	).toBeVisible();
	await modal.getByPlaceholder("e.g. The Awesome Store").fill(options.vendor);
	await modal
		.locator('input[type="number"][placeholder="0.00"]')
		.fill(options.total);

	if (options.dateTime) {
		await modal.locator('input[type="datetime-local"]').fill(options.dateTime);
	}

	for (const bucketName of options.buckets ?? []) {
		const chip = modal.getByRole("button", {
			name: new RegExp(bucketName, "i"),
		});
		await expect(chip).toBeVisible({ timeout: 15_000 });
		await chip.click();
	}

	await modal.getByRole("button", { name: "Save Receipt" }).click();
	await expect(modal).not.toBeVisible();
}

export async function switchToYear(page: Page, year: string) {
	const yearInput = page.locator('input[type="number"]');
	if (!(await yearInput.isVisible())) {
		await page.getByRole("button", { name: /^Year$/i }).click();
	}
	await expect(page.getByRole("button", { name: /^Year$/i })).toHaveClass(
		/active/,
	);
	await expect(yearInput).toBeVisible();
	await yearInput.fill(year);
	await yearInput.dispatchEvent("change");
	await expect(yearInput).toHaveValue(year);
}

export async function switchToMonth(page: Page, month: string) {
	const monthInput = page.locator('input[type="month"]');
	if (!(await monthInput.isVisible())) {
		await page.getByRole("button", { name: /^Month$/i }).click();
	}
	await expect(page.getByRole("button", { name: /^Month$/i })).toHaveClass(
		/active/,
	);
	await expect(monthInput).toBeVisible();
	await monthInput.fill(month);
	await monthInput.dispatchEvent("change");
	await expect(monthInput).toHaveValue(month);
}
