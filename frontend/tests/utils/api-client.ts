import { TaxosApiClient } from "../../src/api/client";
import fs from "fs";
import path from "path";

// Re-export the main client class configured for testing
export { TaxosApiClient };

/**
 * Resolves the dev access token dynamically:
 * 1. TAXOS_ACCESS_TOKEN env var (for CI / overrides)
 * 2. Reads the token from backend/data/access_tokens/ that matches the
 *    default tenant in backend/data/default_context.json
 */
function resolveAccessToken(): string {
	if (process.env.TAXOS_ACCESS_TOKEN) {
		return process.env.TAXOS_ACCESS_TOKEN;
	}

	const dataDir = path.resolve(__dirname, "../../../backend/data");
	const contextFile = path.join(dataDir, "default_context.json");
	if (!fs.existsSync(contextFile)) {
		throw new Error("No default_context.json found. Did you run dev.seed?");
	}

	const { tenant: tenantGuid } = JSON.parse(
		fs.readFileSync(contextFile, "utf-8"),
	);

	const tokensDir = path.join(dataDir, "access_tokens");
	const tokenFiles = fs
		.readdirSync(tokensDir)
		.filter((f) => f.endsWith(".json"));

	for (const file of tokenFiles) {
		const content = JSON.parse(
			fs.readFileSync(path.join(tokensDir, file), "utf-8"),
		);
		if (content.tenant === tenantGuid) {
			return path.basename(file, ".json");
		}
	}

	throw new Error(
		`No access token found for default tenant ${tenantGuid}. Did you run dev.seed?`,
	);
}

// Create a test client instance with default test configuration
export const createTestClient = (options?: {
	baseUrl?: string;
	token?: string;
}) => {
	return new TaxosApiClient({
		baseUrl:
			options?.baseUrl ||
			process.env.VITE_GRPC_API_URL ||
			"http://localhost:50051",
		token: options?.token || resolveAccessToken(),
	});
};
