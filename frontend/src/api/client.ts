/* eslint-disable @typescript-eslint/no-explicit-any */
import {
	ApolloClient,
	InMemoryCache,
	HttpLink,
	ApolloLink,
	from,
	gql,
} from "@apollo/client";

// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------

export const getToken = () => localStorage.getItem("taxos_token");

export const setToken = (token: string) => {
	localStorage.setItem("taxos_token", token);
	window.location.reload();
};

export const clearToken = () => {
	localStorage.removeItem("taxos_token");
	window.location.reload();
};

// ---------------------------------------------------------------------------
// Apollo Client
// ---------------------------------------------------------------------------

const authLink = new ApolloLink((operation, forward) => {
	const token = getToken();
	if (token) {
		operation.setContext(({ headers = {} }) => ({
			headers: { ...headers, Authorization: `Bearer ${token}` },
		}));
	}
	return forward(operation);
});

const httpLink = new HttpLink({ uri: "/graphql" });

const apolloClient = new ApolloClient({
	link: from([authLink, httpLink]),
	cache: new InMemoryCache(),
	defaultOptions: {
		query: { fetchPolicy: "no-cache" },
		mutate: { fetchPolicy: "no-cache" },
	},
});

// ---------------------------------------------------------------------------
// GraphQL documents
// ---------------------------------------------------------------------------

const LIST_BUCKETS_QUERY = gql`
	query ListBuckets {
		buckets {
			guid
			name
		}
	}
`;

const LIST_RECEIPTS_QUERY = gql`
	query ListReceipts($bucket: ID, $months: [String!], $vendor: ID) {
		receipts(bucket: $bucket, months: $months, vendor: $vendor) {
			guid
			vendor
			total
			date
			timezone
			notes
			hash
			reference
			allocations {
				amount
				bucket {
					guid
				}
			}
		}
	}
`;

const CREATE_BUCKET_MUTATION = gql`
	mutation CreateBucket($name: String!) {
		createBucket(name: $name) {
			guid
			name
		}
	}
`;

const UPDATE_BUCKET_MUTATION = gql`
	mutation UpdateBucket($guid: ID!, $name: String!) {
		updateBucket(guid: $guid, name: $name) {
			guid
			name
		}
	}
`;

const DELETE_BUCKET_MUTATION = gql`
	mutation DeleteBucket($guid: ID!) {
		deleteBucket(guid: $guid)
	}
`;

const RECEIPT_FIELDS = `
  guid vendor total date timezone notes hash reference
  allocations { amount bucket { guid } }
`;

const CREATE_RECEIPT_MUTATION = gql`
  mutation CreateReceipt($input: ReceiptInput!) {
    createReceipt(input: $input) { ${RECEIPT_FIELDS} }
  }
`;

const UPDATE_RECEIPT_MUTATION = gql`
  mutation UpdateReceipt($guid: ID!, $input: ReceiptInput!) {
    updateReceipt(guid: $guid, input: $input) { ${RECEIPT_FIELDS} }
  }
`;

const DELETE_RECEIPT_MUTATION = gql`
	mutation DeleteReceipt($guid: ID!) {
		deleteReceipt(guid: $guid)
	}
`;

const LIST_VENDORS_QUERY = gql`
	query ListVendors {
		vendors {
			guid
			name
		}
	}
`;

const UPDATE_VENDOR_MUTATION = gql`
	mutation UpdateVendor($guid: ID!, $name: String!) {
		updateVendor(guid: $guid, name: $name) {
			guid
			name
		}
	}
`;

const UPLOAD_FILE_MUTATION = gql`
	mutation UploadReceiptFile(
		$hash: String!
		$filename: String!
		$data: String!
	) {
		uploadReceiptFile(hash: $hash, filename: $filename, data: $data) {
			hash
			filename
			alreadyExists
		}
	}
`;

// ---------------------------------------------------------------------------
// Typed API wrapper — same call signatures TaxosContext expects
// ---------------------------------------------------------------------------

type AllocationInput = { bucket: string; amount: number };
type GQLAlloc = { amount: number; bucket: { guid: string } };

function mapAllocationsInput(
	allocations: AllocationInput[],
): { bucketGuid: string; amount: number }[] {
	return allocations.map((a) => ({ bucketGuid: a.bucket, amount: a.amount }));
}

function mapReceiptResponse(r: {
	guid: string;
	vendor: string;
	total: number;
	date: string;
	timezone: string;
	notes?: string | null;
	hash?: string | null;
	reference?: string | null;
	allocations: GQLAlloc[];
}) {
	return {
		guid: r.guid,
		vendor: r.vendor,
		total: r.total,
		date: r.date,
		timezone: r.timezone,
		notes: r.notes ?? "",
		hash: r.hash ?? "",
		vendorRef: r.reference ?? "",
		allocations: r.allocations.map((a) => ({
			bucket: a.bucket.guid,
			amount: a.amount,
		})),
	};
}

export type MappedReceipt = ReturnType<typeof mapReceiptResponse>;

export const client = {
	async listBuckets() {
		const { data = {} as Record<string, any> } = await apolloClient.query<
			Record<string, any>
		>({ query: LIST_BUCKETS_QUERY });
		return {
			buckets: data.buckets as { guid: string; name: string }[],
		};
	},

	async listReceipts(params?: {
		bucket?: string;
		months?: string[];
		vendor?: string;
	}) {
		const { data = {} as Record<string, any> } = await apolloClient.query<
			Record<string, any>
		>({
			query: LIST_RECEIPTS_QUERY,
			variables: {
				bucket: params?.bucket,
				months: params?.months,
				vendor: params?.vendor,
			},
		});
		return { receipts: data.receipts.map(mapReceiptResponse) };
	},

	async createBucket(args: { name: string }) {
		const { data } = await apolloClient.mutate<Record<string, any>>({
			mutation: CREATE_BUCKET_MUTATION,
			variables: { name: args.name },
		});
		return data!.createBucket as { guid: string; name: string };
	},

	async updateBucket(args: { guid: string; name: string }) {
		const { data } = await apolloClient.mutate<Record<string, any>>({
			mutation: UPDATE_BUCKET_MUTATION,
			variables: args,
		});
		return data!.updateBucket as { guid: string; name: string };
	},

	async deleteBucket(args: { guid: string }) {
		await apolloClient.mutate({
			mutation: DELETE_BUCKET_MUTATION,
			variables: args,
		});
	},

	async createReceipt(args: {
		vendor: string;
		total: number;
		date: Date;
		timezone: string;
		allocations?: AllocationInput[];
		vendorRef?: string;
		notes?: string;
		hash?: string;
	}) {
		const dateIso = args.date.toISOString();
		const { data } = await apolloClient.mutate<Record<string, any>>({
			mutation: CREATE_RECEIPT_MUTATION,
			variables: {
				input: {
					vendor: args.vendor,
					total: args.total,
					date: dateIso,
					timezone: args.timezone,
					allocations: mapAllocationsInput(args.allocations ?? []),
					reference: args.vendorRef ?? "",
					notes: args.notes ?? "",
					hash: args.hash ?? "",
				},
			},
		});
		return mapReceiptResponse(data!.createReceipt);
	},

	async updateReceipt(args: {
		guid: string;
		vendor: string;
		total: number;
		date: Date;
		timezone: string;
		allocations?: AllocationInput[];
		vendorRef?: string;
		notes?: string;
		hash?: string;
	}) {
		const dateIso = args.date.toISOString();
		const { data } = await apolloClient.mutate<Record<string, any>>({
			mutation: UPDATE_RECEIPT_MUTATION,
			variables: {
				guid: args.guid,
				input: {
					vendor: args.vendor,
					total: args.total,
					date: dateIso,
					timezone: args.timezone,
					allocations: mapAllocationsInput(args.allocations ?? []),
					reference: args.vendorRef ?? "",
					notes: args.notes ?? "",
					hash: args.hash ?? "",
				},
			},
		});
		return mapReceiptResponse(data!.updateReceipt);
	},

	async deleteReceipt(args: { guid: string }) {
		await apolloClient.mutate({
			mutation: DELETE_RECEIPT_MUTATION,
			variables: args,
		});
	},

	async listVendors() {
		const { data = {} as Record<string, any> } = await apolloClient.query<
			Record<string, any>
		>({ query: LIST_VENDORS_QUERY });
		return {
			vendors: data.vendors as { guid: string; name: string }[],
		};
	},

	async updateVendor(args: { guid: string; name: string }) {
		const { data } = await apolloClient.mutate<Record<string, any>>({
			mutation: UPDATE_VENDOR_MUTATION,
			variables: args,
		});
		return data!.updateVendor as { guid: string; name: string };
	},
};

// ---------------------------------------------------------------------------
// File upload / download
// ---------------------------------------------------------------------------

export const uploadReceiptFile = async (
	file: File,
	hash: string,
	onProgress?: (progress: number) => void,
): Promise<{ alreadyExists: boolean }> => {
	onProgress?.(25);
	const fileBuffer = await file.arrayBuffer();
	const bytes = new Uint8Array(fileBuffer);
	let binary = "";
	for (let i = 0; i < bytes.byteLength; i++)
		binary += String.fromCharCode(bytes[i]);
	const base64 = btoa(binary);
	onProgress?.(60);
	const { data } = await apolloClient.mutate<Record<string, any>>({
		mutation: UPLOAD_FILE_MUTATION,
		variables: { hash, filename: file.name, data: base64 },
	});
	onProgress?.(100);
	return { alreadyExists: data!.uploadReceiptFile.alreadyExists };
};

export const downloadReceiptFile = async (
	fileHash: string,
): Promise<{ filename: string; fileSize: number }> => {
	const token = getToken();
	const response = await fetch(`/files/${fileHash}`, {
		headers: token ? { Authorization: `Bearer ${token}` } : {},
	});
	if (!response.ok) throw new Error(`Download failed: ${response.statusText}`);

	const contentDisposition = response.headers.get("Content-Disposition") ?? "";
	const filenameMatch = contentDisposition.match(/filename="([^"]+)"/);
	const filename = filenameMatch?.[1] ?? fileHash;
	const blob = await response.blob();

	const url = window.URL.createObjectURL(blob);
	const link = document.createElement("a");
	link.href = url;
	link.download = filename;
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	window.URL.revokeObjectURL(url);

	return { filename, fileSize: blob.size };
};
