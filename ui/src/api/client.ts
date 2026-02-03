import { type Bucket, type Receipt, type DashboardResponse, BucketSchema, ReceiptSchema, DashboardResponseSchema, BucketSummarySchema } from './gen/taxos_service_pb';
import { create } from '@bufbuild/protobuf';

// Mock data for testing
const mockBuckets: Bucket[] = [
  create(BucketSchema, {
    guid: '1',
    name: 'Office Supplies'
  }),
  create(BucketSchema, {
    guid: '2',
    name: 'Travel Expenses'
  })
];

class TaxosApiClient {
  async createBucket(name: string): Promise<Bucket> {
    const newBucket = create(BucketSchema, {
      guid: Math.random().toString(36).substr(2, 9),
      name
    });
    mockBuckets.push(newBucket);
    return newBucket;
  }

  async getBucket(guid: string): Promise<Bucket> {
    const bucket = mockBuckets.find(b => b.guid === guid);
    if (!bucket) throw new Error('Bucket not found');
    return bucket;
  }

  async listBuckets(_options: {
    startDate?: Date;
    endDate?: Date;
    includeEmpty?: boolean;
  } = {}): Promise<{ buckets: Array<{ bucket: Bucket; totalAmount: number; receiptCount: number }> }> {
    const bucketSummaries = mockBuckets.map(bucket => ({
      bucket,
      totalAmount: Math.random() * 100, // Mock amount
      receiptCount: Math.floor(Math.random() * 10) // Mock count
    }));

    return { buckets: bucketSummaries };
  }

  async updateBucket(guid: string, name: string): Promise<Bucket> {
    const bucket = mockBuckets.find(b => b.guid === guid);
    if (!bucket) throw new Error('Bucket not found');
    bucket.name = name;
    return bucket;
  }

  async deleteBucket(guid: string): Promise<boolean> {
    const index = mockBuckets.findIndex(b => b.guid === guid);
    if (index === -1) return false;
    mockBuckets.splice(index, 1);
    return true;
  }

  async getDashboard(options: {
    startDate?: Date;
    endDate?: Date;
    includeEmptyBuckets?: boolean;
  } = {}): Promise<DashboardResponse> {
    const bucketsResponse = await this.listBuckets(options);

    const totalAmount = bucketsResponse.buckets.reduce((sum, b) => sum + b.totalAmount, 0);
    const totalReceipts = bucketsResponse.buckets.reduce((sum, b) => sum + b.receiptCount, 0);

    const bucketSummaries = bucketsResponse.buckets.map(summary =>
      create(BucketSummarySchema, {
        bucket: summary.bucket,
        totalAmount: summary.totalAmount,
        receiptCount: summary.receiptCount
      })
    );

    return create(DashboardResponseSchema, {
      bucketSummaries,
      totalAmount,
      totalReceipts
    });
  }

  async ingestReceipt(bucketGuid: string, _content: Uint8Array, filename: string): Promise<Receipt> {
    return create(ReceiptSchema, {
      guid: Math.random().toString(36).substr(2, 9),
      bucketGuid,
      description: `Receipt from ${filename}`,
      amount: Math.random() * 100
    });
  }
}

// Export singleton instance
export const taxosApiClient = new TaxosApiClient();

// Export types for use in components
export type {
  Bucket,
  Receipt,
  DashboardResponse
} from './generated/taxos_service_pb';

// Helper interface for compatibility with existing code
export interface CreateBucketRequest {
  name: string;
}

// Default export for backward compatibility
export default taxosApiClient;