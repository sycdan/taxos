import { TaxosApiClient } from "../../src/api/client";

// Re-export the main client class configured for testing
export { TaxosApiClient };

// Create a test client instance with default test configuration
export const createTestClient = (options?: {
	baseUrl?: string;
	token?: string;
}) => {
	return new TaxosApiClient({
		baseUrl: options?.baseUrl || process.env.VITE_GRPC_API_URL || "http://localhost:50051",
		token:
			options?.token ||
			"4afd1cc3691d44d7bf94612660de9c14",
	});
};
