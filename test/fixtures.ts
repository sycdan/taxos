import { test as base, expect } from "@playwright/test";
import { execSync } from "child_process";

const SCAF = `PYTHONPATH=/workspaces/taxos/backend scaf call /workspaces/taxos/backend`;

export type TestTenant = {
	token: string;
	tenantGuid: string;
};

/**
 * Extends the base Playwright `test` with a `tenant` fixture.
 *
 * Each test that declares `tenant` gets a freshly provisioned tenant with no
 * data. The tenant (and its access token) is deleted after the test completes,
 * regardless of pass/fail.
 *
 * The fixture also injects the token into the browser's localStorage before
 * any navigation, so the app loads as authenticated without going through the
 * login modal.
 */
export const test = base.extend<{ tenant: TestTenant }>({
	tenant: async ({ page }, use) => {
		// Create tenant, then generate an access token for it.
		const tenantJson = JSON.parse(
			execSync(`${SCAF}/taxos/tenant/create "E2E Flow Test"`, {
				encoding: "utf-8",
			}),
		);
		const tenantGuid: string = tenantJson.guid;

		const tokenJson = JSON.parse(
			execSync(`${SCAF}/taxos/access/token/generate "${tenantGuid}"`, {
				encoding: "utf-8",
			}),
		);
		const token: string = tokenJson.key;

		// Inject token before the page loads so the app boots as authenticated.
		await page.addInitScript((t: string) => {
			localStorage.setItem("taxos_token", t);
		}, token);

		await use({ token, tenantGuid });

		// Teardown — sudo because the backend container creates root-owned subdirs.
		execSync(`sudo ${SCAF}/taxos/tenant/delete "${tenantGuid}"`);
	},
});

export { expect };
