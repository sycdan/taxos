import { createClient, type Interceptor } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";
import { TaxosApi } from "../../src/api/v1/taxos_service_connect";

export class TaxosApiClient {
	private client: ReturnType<typeof createClient<typeof TaxosApi>>;

	constructor(
		private baseUrl: string = "http://backend:50051",
		private token: string = "65d2d4bb66af87ec6fc9dd5d9436e9b259eddb90724a9b22d089b4971e44cb53",
	) {
		// Create an interceptor that adds the token to requests
		const tokenInterceptor: Interceptor = (next) => async (req) => {
			req.header.set("Authorization", `Bearer ${this.token}`);
			return await next(req);
		};

		this.client = createClient(
			TaxosApi,
			createConnectTransport({
				baseUrl: this.baseUrl,
				interceptors: [tokenInterceptor],
			}),
		);
	}

	async listBuckets() {
		return await this.client.listBuckets({});
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

	async createReceipt(
		total: number,
		vendor: string,
		notes?: string,
		allocations?: Array<{ bucket: string; amount: number }>,
	) {
		const date = new Date();
		return await this.client.createReceipt({
			total,
			vendor,
			date: {
				seconds: BigInt(Math.floor(date.getTime() / 1000)),
				nanos: (date.getTime() % 1000) * 1_000_000,
			},
			timezone: "UTC",
			notes: notes || "",
			allocations: allocations || [],
		});
	}

	async listUnallocatedReceipts() {
		return await this.client.listReceipts({});
	}

	async listReceiptsForBucket(bucketGuid: string) {
		return await this.client.listReceipts({ bucket: bucketGuid });
	}
}
