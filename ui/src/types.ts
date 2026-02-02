export interface Bucket {
  id: string;
  name: string;
}

export interface ReceiptAllocation {
  bucketId: string;
  amount: number;
}

export interface Receipt {
  id: string;
  vendor: string;
  date: string; // ISO8601 with offset
  timezone: string;
  total: number;
  allocations: ReceiptAllocation[];
  ref?: string;
  notes?: string;
  file?: string; // filename or stub
  hash?: string; // SHA-256 hash for duplicate prevention
}

export const UNALLOCATED_BUCKET_ID = 'unallocated';
