import { createClient, type Interceptor, Code } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";
import { TaxosApi } from "./v1/taxos_service_connect";

const logoutOnUnauthorized = () => {
	localStorage.removeItem("taxos_token");
	window.location.href = "/";
};

export class TaxosApiClient {
	private client: ReturnType<typeof createClient<typeof TaxosApi>>;
	private getToken: () => string | null;
	private onUnauthorized?: () => void;

	constructor(options?: {
		baseUrl?: string;
		token?: string;
		getToken?: () => string | null;
		onUnauthorized?: () => void;
	}) {
		const baseUrl =
			options?.baseUrl ||
			import.meta.env.VITE_GRPC_API_URL ||
			"http://localhost:8080";

		// For testing: fixed token; for app: dynamic from localStorage
		this.getToken = options?.getToken || (() => options?.token || null);
		this.onUnauthorized = options?.onUnauthorized;

		// Create an interceptor that adds the token to requests
		const tokenInterceptor: Interceptor = (next) => async (req) => {
			const token = this.getToken();
			if (token) {
				req.header.set("Authorization", `Bearer ${token}`);
			}

			try {
				return await next(req);
			} catch (error: unknown) {
				const err = error as { code?: Code; status?: number } | null;
				// Check if it's a 401/Unauthenticated error
				if (err?.code === Code.Unauthenticated || err?.status === 401) {
					this.onUnauthorized?.();
				}
				throw error;
			}
		};

		this.client = createClient(
			TaxosApi,
			createConnectTransport({
				baseUrl,
				interceptors: [tokenInterceptor],
			}),
		);
	}

	// Bucket methods
	async getDashboard(params?: { months?: string[] }) {
		return await this.client.getDashboard(params || {});
	}

	async createBucket(name: string) {
		return await this.client.createBucket({ name });
	}

	async getBucket(guid: string) {
		return await this.client.getBucket({ guid });
	}

	async updateBucket(guid: string, name: string) {
		return await this.client.updateBucket({ guid, name });
	}

	async deleteBucket(guid: string) {
		return await this.client.deleteBucket({ guid });
	}

	// Receipt methods
	async createReceipt(
		total: number,
		vendor: string,
		notes?: string,
		allocations?: Array<{ bucket: string; amount: number }>,
		date?: Date,
	) {
		const receiptDate = date || new Date();
		return await this.client.createReceipt({
			total,
			vendor,
			date: dateToTimestamp(receiptDate),
			timezone: "UTC",
			notes: notes || "",
			allocations: allocations || [],
		});
	}

	async updateReceipt(params: {
		guid: string;
		vendor?: string;
		total?: number;
		notes?: string;
		allocations?: Array<{ bucket: string; amount: number }>;
		date?: Date;
	}) {
		return await this.client.updateReceipt({
			guid: params.guid,
			vendor: params.vendor || "",
			total: params.total || 0,
			date: params.date ? dateToTimestamp(params.date) : undefined,
			timezone: "UTC",
			notes: params.notes || "",
			allocations: params.allocations || [],
		});
	}

	async listReceipts(params?: { bucket?: string; months?: string[] }) {
		return await this.client.listReceipts(params || {});
	}

	async deleteReceipt(guid: string) {
		return await this.client.deleteReceipt({ guid });
	}

	// File upload/download with browser-specific logic
	async uploadReceiptFile(
		file: File,
		hash: string,
		onProgress?: (progress: number) => void,
	) {
		try {
			// Convert file to Uint8Array for protobuf bytes field
			const fileBuffer = await file.arrayBuffer();
			const fileBytes = new Uint8Array(fileBuffer);

			// Simulate progress for the encoding step
			onProgress?.(25);

			const response = await this.client.uploadReceiptFile({
				fileHash: hash,
				filename: file.name,
				fileData: fileBytes,
			});

			onProgress?.(100);

			return {
				alreadyExists: response.alreadyExists,
				fileInfo: response.fileInfo
					? {
							fileHash: response.fileInfo.fileHash,
							filename: response.fileInfo.filename,
							filePath: response.fileInfo.filePath,
							fileSize: Number(response.fileInfo.fileSize),
							uploadedAt: response.fileInfo.uploadedAt,
						}
					: undefined,
			};
		} catch (error) {
			onProgress?.(0);
			throw error;
		}
	}

	async downloadReceiptFile(fileHash: string) {
		try {
			const response = await this.client.downloadReceiptFile({
				fileHash: fileHash,
			});

			// fileData is already a Uint8Array from protobuf
			const blob = new Blob([response.fileData]);

			// Create download link
			const url = window.URL.createObjectURL(blob);
			const link = document.createElement("a");
			link.href = url;
			link.download = response.filename;
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
			window.URL.revokeObjectURL(url);

			return {
				filename: response.filename,
				fileSize: Number(response.fileSize),
			};
		} catch (error) {
			throw error;
		}
	}

	// Direct access to underlying client for advanced usage
	get rawClient() {
		return this.client;
	}
}

// Default client instance for the app
const defaultClient = new TaxosApiClient({
	getToken: () => localStorage.getItem("taxos_token"),
	onUnauthorized: logoutOnUnauthorized,
});

// Export the raw Connect-RPC client for contexts that expect it
export const client = defaultClient.rawClient;

// Helper to convert Date to Timestamp
export const dateToTimestamp = (date: Date) => {
	const seconds = BigInt(Math.floor(date.getTime() / 1000));
	const nanos = (date.getTime() % 1000) * 1_000_000;
	return { seconds, nanos };
};

// Convenience exports for the default client instance
export const getToken = () => localStorage.getItem("taxos_token");

export const setToken = (token: string) => {
	localStorage.setItem("taxos_token", token);
	window.location.reload();
};

export const clearToken = () => {
	localStorage.removeItem("taxos_token");
	window.location.reload();
};

// Re-export file upload/download methods as standalone functions
export const uploadReceiptFile = (
	file: File,
	hash: string,
	onProgress?: (progress: number) => void,
) => defaultClient.uploadReceiptFile(file, hash, onProgress);

export const downloadReceiptFile = (fileHash: string) =>
	defaultClient.downloadReceiptFile(fileHash);
