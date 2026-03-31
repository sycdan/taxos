import { test, expect } from "../fixtures";
import path from "path";
import fs from "fs";
import os from "os";

test.describe("File Attachment Flow", () => {
	test("uploading a file via the Upload File button opens receipt modal with the file attached", async ({
		page,
		tenant: _tenant,
	}) => {
		// Create a temp file unique to this test run so uploads never collide.
		const tmpPath = path.join(
			os.tmpdir(),
			`taxos-upload-test-${Date.now()}.txt`,
		);
		fs.writeFileSync(tmpPath, `Taxos upload test ${Date.now()}`);

		await page.goto("/");
		await expect(page.getByText("TAXOS")).toBeVisible();

		// Set files directly on the hidden file input — more reliable in headless
		// Chromium than intercepting the OS file-chooser dialog.
		await page.locator("#file-upload").setInputFiles(tmpPath);

		// Receipt modal should open automatically after the file is processed.
		const modal = page.locator(".modal-overlay");
		await expect(modal).toBeVisible({ timeout: 15_000 });
		await expect(
			modal.getByRole("heading", { name: "New Receipt" }),
		).toBeVisible();

		// Upload progress widget confirms the file was uploaded (shows filename).
		const filename = path.basename(tmpPath);
		await expect(modal.getByText(filename)).toBeVisible({ timeout: 15_000 });

		// Complete the receipt form and save
		await modal.getByPlaceholder("e.g. The Awesome Store").fill("Test Vendor");
		await modal
			.locator('input[type="number"][placeholder="0.00"]')
			.fill("55.00");
		await modal.getByRole("button", { name: "Save Receipt" }).click();
		await expect(modal).not.toBeVisible();

		// The receipt now shows up in the Unallocated bucket (no allocation chosen).
		const unallocatedCard = page.locator(".card", {
			has: page.getByText("Unallocated"),
		});
		await expect(unallocatedCard).toContainText("$55.00");

		// Navigate into Unallocated to confirm receipt has the file attached.
		await unallocatedCard.click();
		const receiptRow = page.locator(".card", {
			has: page.getByText("$55.00"),
		});
		await expect(receiptRow).toBeVisible();

		// Open the receipt — "Attached File" section should be present.
		await receiptRow.click();
		const editModal = page.locator(".modal-overlay");
		await expect(editModal).toBeVisible();
		await expect(editModal.getByText("Attached File")).toBeVisible();
		await expect(
			editModal.getByRole("button", { name: "Download" }),
		).toBeVisible();

		fs.unlinkSync(tmpPath);
	});

	test("uploading the same file a second time does not create a duplicate (upload widget does not error)", async ({
		page,
		tenant: _tenant,
	}) => {
		// A fixed-content file so both uploads share the same hash.
		const tmpPath = path.join(os.tmpdir(), `taxos-dup-test-${Date.now()}.txt`);
		const content = `Duplicate check ${Date.now()}`;
		fs.writeFileSync(tmpPath, content);
		const filename = path.basename(tmpPath);

		await page.goto("/");
		await expect(page.getByText("TAXOS")).toBeVisible();

		// ── First upload ──────────────────────────────────────────────────────
		await page.locator("#file-upload").setInputFiles(tmpPath);

		const modal = page.locator(".modal-overlay");
		await expect(modal).toBeVisible({ timeout: 15_000 });
		await expect(modal.getByText(filename)).toBeVisible({ timeout: 15_000 });

		// Save the first receipt
		await modal
			.getByPlaceholder("e.g. The Awesome Store")
			.fill("First Upload Vendor");
		await modal
			.locator('input[type="number"][placeholder="0.00"]')
			.fill("10.00");
		await modal.getByRole("button", { name: "Save Receipt" }).click();
		await expect(modal).not.toBeVisible();

		// ── Second upload (same file / same hash) ─────────────────────────────
		await page.locator("#file-upload").setInputFiles(tmpPath);

		await expect(modal).toBeVisible({ timeout: 15_000 });

		// The upload widget should show a success state (no error) — the backend
		// silently accepts duplicates and responds with alreadyExists=true.
		await expect(modal.getByText(filename)).toBeVisible({ timeout: 15_000 });
		await expect(modal.getByText(/upload failed/i)).not.toBeVisible();

		// Dismiss without saving — click the X button in the modal header.
		await modal
			.getByRole("button")
			.filter({ has: page.locator("svg") })
			.first()
			.click();
		await expect(modal).not.toBeVisible();

		fs.unlinkSync(tmpPath);
	});
});
