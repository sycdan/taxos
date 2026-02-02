// Mock TypeScript types and client for testing
export interface Bucket {
  id: string;
  name: string;
  description: string;
  createdAt: bigint;
  updatedAt: bigint;
}

export interface Receipt {
  id: string;
  bucketId: string;
  description: string;
  amount: number;
  date: bigint;
  imageUrl: string;
  metadata: Record<string, string>;
  createdAt: bigint;
  updatedAt: bigint;
}

export interface CreateBucketRequest {
  name: string;
  description: string;
}

export interface DashboardResponse {
  bucketSummaries: Array<{
    bucket: Bucket;
    totalAmount: number;
    receiptCount: number;
  }>;
  totalAmount: number;
  totalReceipts: number;
}

// Mock data for testing
const mockBuckets: Bucket[] = [
  {
    id: '1',
    name: 'Office Supplies',
    description: 'Pens, paper, and other office items',
    createdAt: BigInt(Date.now()),
    updatedAt: BigInt(Date.now())
  },
  {
    id: '2',
    name: 'Travel Expenses',
    description: 'Business travel costs',
    createdAt: BigInt(Date.now()),
    updatedAt: BigInt(Date.now())
  }
];

const mockReceipts: Receipt[] = [
  {
    id: 'r1',
    bucketId: '1',
    description: 'Printer paper',
    amount: 25.99,
    date: BigInt(Date.now() - 86400000), // Yesterday
    imageUrl: '',
    metadata: {},
    createdAt: BigInt(Date.now()),
    updatedAt: BigInt(Date.now())
  },
  {
    id: 'r2',
    bucketId: '1',
    description: 'Pen set',
    amount: 12.50,
    date: BigInt(Date.now() - 172800000), // 2 days ago
    imageUrl: '',
    metadata: {},
    createdAt: BigInt(Date.now()),
    updatedAt: BigInt(Date.now())
  },
  {
    id: 'r3',
    bucketId: '2',
    description: 'Hotel accommodation',
    amount: 150.00,
    date: BigInt(Date.now() - 259200000), // 3 days ago
    imageUrl: '',
    metadata: {},
    createdAt: BigInt(Date.now()),
    updatedAt: BigInt(Date.now())
  }
];

class MockTaxosApiClient {
  private buckets: Bucket[] = [...mockBuckets];
  private receipts: Receipt[] = [...mockReceipts];

  async createBucket(name: string, description?: string): Promise<Bucket> {
    const bucket: Bucket = {
      id: Math.random().toString(36).substr(2, 9),
      name,
      description: description || '',
      createdAt: BigInt(Date.now()),
      updatedAt: BigInt(Date.now())
    };
    this.buckets.push(bucket);
    return bucket;
  }

  async getBucket(id: string): Promise<Bucket> {
    const bucket = this.buckets.find(b => b.id === id);
    if (!bucket) throw new Error('Bucket not found');
    return bucket;
  }

  async listBuckets(options: {
    startDate?: Date;
    endDate?: Date;
    includeEmpty?: boolean;
  } = {}): Promise<{ buckets: Array<{ bucket: Bucket; totalAmount: number; receiptCount: number }> }> {
    const startMs = options.startDate ? BigInt(options.startDate.getTime()) : 0n;
    const endMs = options.endDate ? BigInt(options.endDate.getTime()) : BigInt(Date.now());

    const bucketSummaries = this.buckets.map(bucket => {
      const bucketReceipts = this.receipts.filter(r =>
        r.bucketId === bucket.id &&
        r.date >= startMs &&
        r.date <= endMs
      );

      const totalAmount = bucketReceipts.reduce((sum, r) => sum + r.amount, 0);
      const receiptCount = bucketReceipts.length;

      return {
        bucket,
        totalAmount,
        receiptCount
      };
    }).filter(summary => options.includeEmpty || summary.receiptCount > 0);

    return { buckets: bucketSummaries };
  }

  async getDashboard(options: {
    startDate?: Date;
    endDate?: Date;
    includeEmptyBuckets?: boolean;
  } = {}): Promise<DashboardResponse> {
    const bucketsResponse = await this.listBuckets(options);

    const totalAmount = bucketsResponse.buckets.reduce((sum, b) => sum + b.totalAmount, 0);
    const totalReceipts = bucketsResponse.buckets.reduce((sum, b) => sum + b.receiptCount, 0);

    return {
      bucketSummaries: bucketsResponse.buckets,
      totalAmount,
      totalReceipts
    };
  }
}

// Create a singleton instance
const apiClient = new MockTaxosApiClient();

export default apiClient;