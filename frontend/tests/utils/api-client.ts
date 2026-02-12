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
			"65d2d4bb66af87ec6fc9dd5d9436e9b259eddb90724a9b22d089b4971e44cb53",
	});
};
