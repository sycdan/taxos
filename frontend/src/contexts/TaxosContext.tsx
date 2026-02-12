import React, { createContext, useContext, useState, useEffect, useCallback, useMemo, type ReactNode } from 'react';
import { Timestamp } from '@bufbuild/protobuf';
import type { Bucket, BucketSummary, Receipt } from '../types';
import { client, getToken } from '../api/client';

const slugify = (text: string) => {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
};

interface TaxosContextType {
  buckets: Bucket[];
  bucketSummaries: BucketSummary[];
  unallocatedSummary: { totalAmount: number; receiptCount: number };
  receipts: Record<string, Receipt>;
  unallocatedReceipts: Receipt[];
  currentReceiptsList: Receipt[];
  loading: boolean;
  authenticated: boolean;
  isNameTaken: (name: string, excludeId?: string) => boolean;
  addBucket: (name: string) => Promise<boolean>;
  updateBucket: (id: string, name: string) => Promise<boolean>;
  deleteBucket: (id: string) => Promise<void>;
  addReceipt: (receipt: Omit<Receipt, 'id'>) => Promise<void>;
  updateReceipt: (receipt: Receipt) => Promise<void>;
  deleteReceipt: (id: string) => Promise<void>;
  refreshBuckets: (startDate?: Date, endDate?: Date, force?: boolean) => Promise<void>;
  loadReceiptsForBucket: (bucketId: string, startDate: Date, endDate: Date) => Promise<Receipt[]>;
  getUnallocatedReceipts: (startDate: Date, endDate: Date) => Promise<Receipt[]>;
}

const TaxosContext = createContext<TaxosContextType | undefined>(undefined);

export const TaxosProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [buckets, setBuckets] = useState<Bucket[]>([]);
  const [bucketSummaries, setBucketSummaries] = useState<BucketSummary[]>([]);
  const [unallocatedSummary, setUnallocatedSummary] = useState<{ totalAmount: number; receiptCount: number }>({ totalAmount: 0, receiptCount: 0 });
  const [receipts, setReceipts] = useState<Record<string, Receipt>>({});
  const [unallocatedReceipts, setUnallocatedReceipts] = useState<Receipt[]>([]);
  const [currentReceiptsList, setCurrentReceiptsList] = useState<Receipt[]>([]);

  // Track receipt hashes for O(1) duplicate detection
  const receiptHashes = useMemo(() => {
    const hashes = new Set<string>();
    Object.values(receipts).forEach(r => {
      if (r.hash) hashes.add(r.hash);
    });
    return hashes;
  }, [receipts]);
  const [loading, setLoading] = useState(true);
  const [authenticated] = useState(!!getToken());
  const [currentDateFilter, setCurrentDateFilter] = useState<{ start?: Date, end?: Date }>({});

  // Helper to convert Timestamp to ISO string
  const timestampToIso = (ts?: Timestamp) => {
    if (!ts) return new Date().toISOString();
    const asAny = ts as any;
    if (typeof asAny.toDate === 'function') return asAny.toDate().toISOString();
    const seconds = Number(asAny.seconds ?? 0);
    const nanos = Number(asAny.nanos ?? 0);
    return new Date(seconds * 1000 + nanos / 1_000_000).toISOString();
  };

  // Helper to generate "yyyy-mm" strings for a range
  const getMonthsInRange = (start?: Date, end?: Date): string[] => {
    if (!start || !end) return [];
    const months: string[] = [];
    let current = new Date(start.getFullYear(), start.getMonth(), 1);
    const last = new Date(end.getFullYear(), end.getMonth(), 1);

    while (current <= last) {
      const year = current.getFullYear();
      const month = String(current.getMonth() + 1).padStart(2, '0');
      months.push(`${year}-${month}`);
      current.setMonth(current.getMonth() + 1);
    }
    return months;
  };

  const refreshBuckets = useCallback(async (startDate?: Date, endDate?: Date, force?: boolean) => {
    // Only refresh if dates have actually changed or it's the initial load
    const sameStart = (!startDate && !currentDateFilter.start) || (startDate && currentDateFilter.start && startDate.getTime() === currentDateFilter.start.getTime());
    const sameEnd = (!endDate && !currentDateFilter.end) || (endDate && currentDateFilter.end && endDate.getTime() === currentDateFilter.end.getTime());

    if (!force && sameStart && sameEnd && buckets.length > 0) {
      console.log('Skipping GetDashboard - same date filter and buckets already loaded');
      return;
    }

    try {
      setLoading(true);
      if (!authenticated) {
        setLoading(false);
        return;
      }

      console.log('Making GetDashboard request with date filter change...');
      setCurrentDateFilter({ start: startDate, end: endDate });

      const response = await client.getDashboard({
        months: getMonthsInRange(startDate, endDate),
      });

      const apiBuckets: Bucket[] = response.buckets.map(summary => ({
        id: summary.guid,
        name: summary.name
      }));

      const apiSummaries: BucketSummary[] = response.buckets.map(summary => ({
        bucket: {
          id: summary.guid,
          name: summary.name
        },
        totalAmount: summary.totalAmount,
        receiptCount: summary.receiptCount
      }));

      const apiUnallocatedReceipts: Receipt[] = response.unallocatedReceipts.map(r => ({
        id: r.guid,
        vendor: r.vendor,
        total: r.total,
        date: timestampToIso(r.date),
        timezone: r.timezone,
        allocations: r.allocations.map(a => ({
          bucketId: a.bucket,
          amount: a.amount,
        })),
        ref: r.vendorRef || undefined,
        notes: r.notes || undefined,
        hash: r.hash || undefined,
      }));

      // Calculate unallocated portions for the pseudo-bucket summary
      let unallocatedTotal = 0;
      let unallocatedCount = 0;

      for (const r of apiUnallocatedReceipts) {
        const allocatedAmount = r.allocations.reduce((sum, a) => sum + a.amount, 0);
        const unallocatedAmount = r.total - allocatedAmount;
        if (unallocatedAmount > 0) {
          unallocatedTotal += unallocatedAmount;
          unallocatedCount++;
        }
      }

      setBuckets(apiBuckets);
      setBucketSummaries(apiSummaries);
      setUnallocatedReceipts(apiUnallocatedReceipts);
      setUnallocatedSummary({ totalAmount: unallocatedTotal, receiptCount: unallocatedCount });
      
      // Default view is unallocated if no specific bucket is being loaded
      setCurrentReceiptsList(apiUnallocatedReceipts);

      // Update cache
      setReceipts(prev => {
        const updated = { ...prev };
        for (const r of apiUnallocatedReceipts) {
          updated[r.id] = r;
        }
        return updated;
      });

    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  }, [authenticated, currentDateFilter, buckets.length]);

  // Don't load buckets on mount - let Dashboard call refreshBuckets with date filter
  useEffect(() => {
    if (!authenticated) {
      setLoading(false);
    } else {
      setLoading(false);
    }
  }, [authenticated]);

  const triggerRefresh = useCallback(() => {
    if (currentDateFilter.start || currentDateFilter.end) {
      void refreshBuckets(currentDateFilter.start, currentDateFilter.end, true);
    }
  }, [currentDateFilter, refreshBuckets]);

  const isNameTaken = (name: string, excludeId?: string) => {
    const slug = slugify(name);
    return buckets.some(b => b.id !== excludeId && slugify(b.name) === slug);
  };

  const addBucket = async (name: string) => {
    if (isNameTaken(name)) return false;

    try {
      const response = await client.createBucket({ name });
      const newBucket: Bucket = {
        id: response.guid,
        name: response.name
      };
      setBuckets(prev => [...prev, newBucket]);
      triggerRefresh();
      return true;
    } catch (error) {
      console.error('Failed to create bucket:', error);
      return false;
    }
  };

  const updateBucket = async (id: string, name: string) => {
    if (isNameTaken(name, id)) return false;

    try {
      await client.updateBucket({ guid: id, name });
      setBuckets(prev => prev.map(b => b.id === id ? { ...b, name } : b));
      return true;
    } catch (error) {
      console.error('Failed to update bucket:', error);
      return false;
    }
  };

  const deleteBucket = async (id: string) => {
    try {
      await client.deleteBucket({ guid: id });
      setBuckets(prev => prev.filter(b => b.id !== id));
      setReceipts(prev => {
        const updated = { ...prev };
        for (const key in updated) {
          updated[key] = {
            ...updated[key],
            allocations: updated[key].allocations.filter(a => a.bucketId !== id)
          };
        }
        return updated;
      });
    } catch (error) {
      console.error('Failed to delete bucket:', error);
    }
  };

  const addReceipt = async (receipt: Omit<Receipt, 'id'>) => {
    const toTimestamp = (iso: string) => {
      const date = new Date(iso);
      const seconds = BigInt(Math.floor(date.getTime() / 1000));
      const nanos = (date.getTime() % 1000) * 1_000_000;
      return new Timestamp({ seconds, nanos });
    };

    try {
      const response = await client.createReceipt({
        vendor: receipt.vendor,
        total: receipt.total,
        date: toTimestamp(receipt.date),
        timezone: receipt.timezone,
        allocations: receipt.allocations.map(a => ({
          bucket: a.bucketId,
          amount: a.amount,
        })),
        vendorRef: receipt.ref || '',
        notes: receipt.notes || '',
        hash: receipt.hash || '',
      });

      const createdReceipt: Receipt = {
        id: response.guid,
        vendor: response.vendor,
        total: response.total,
        date: timestampToIso(response.date),
        timezone: response.timezone,
        allocations: response.allocations.map(a => ({
          bucketId: a.bucket,
          amount: a.amount,
        })),
        ref: response.vendorRef || undefined,
        notes: response.notes || undefined,
        hash: response.hash || undefined,
      };

      if (createdReceipt.hash && receiptHashes.has(createdReceipt.hash)) {
        console.warn('Duplicate receipt detected, skipping:', createdReceipt.vendor);
        return;
      }
      setReceipts(prev => ({ ...prev, [createdReceipt.id]: createdReceipt }));
      triggerRefresh();
    } catch (error) {
      console.error('Failed to create receipt:', error);
    }
  };

  const updateReceipt = async (receipt: Receipt) => {
    // Send ISO string for date (not protobuf Timestamp)
    const toIsoString = (iso: string) => {
      return new Date(iso).toISOString();
    };

    // Save previous state for rollback
    const previousReceipt = receipts[receipt.id];

    // Optimistically update local state
    setReceipts(prev => ({ ...prev, [receipt.id]: receipt }));

    try {
      const response = await client.updateReceipt({
        guid: receipt.id,
        vendor: receipt.vendor,
        total: receipt.total,
        date: toIsoString(receipt.date),
        timezone: receipt.timezone,
        allocations: receipt.allocations.map(a => ({
          bucket: a.bucketId,
          amount: a.amount,
        })),
        vendorRef: receipt.ref || '',
        notes: receipt.notes || '',
        hash: receipt.hash || '',
      });

      const updatedReceipt: Receipt = {
        id: response.guid,
        vendor: response.vendor,
        total: response.total,
        date: timestampToIso(response.date),
        timezone: response.timezone,
        allocations: response.allocations.map(a => ({
          bucketId: a.bucket,
          amount: a.amount,
        })),
        ref: response.vendorRef || '',
        notes: response.notes || '',
        hash: response.hash || '',
      };

      setReceipts(prev => ({ ...prev, [updatedReceipt.id]: updatedReceipt }));
      triggerRefresh();
    } catch (error) {
      console.error('Failed to update receipt:', error);
      // Revert optimistic update
      if (previousReceipt) {
        setReceipts(prev => ({ ...prev, [receipt.id]: previousReceipt }));
      }
    }
  };

  const deleteReceipt = async (id: string) => {
    try {
      await client.deleteReceipt({ guid: id });
      setReceipts(prev => {
        const { [id]: _, ...rest } = prev;
        return rest;
      });
      triggerRefresh();
    } catch (error) {
      console.error('Failed to delete receipt:', error);
    }
  };

  const loadReceiptsForBucket = useCallback(async (bucketId: string, startDate: Date, endDate: Date): Promise<Receipt[]> => {
    try {
      const response = await client.listReceipts({
        bucket: bucketId,
        months: getMonthsInRange(startDate, endDate),
      });

      const bucketReceipts: Receipt[] = response.receipts.map(r => ({
        id: r.guid,
        vendor: r.vendor,
        total: r.total,
        date: timestampToIso(r.date),
        timezone: r.timezone,
        allocations: r.allocations.map(a => ({
          bucketId: a.bucket,
          amount: a.amount,
        })),
        ref: r.vendorRef || undefined,
        notes: r.notes || undefined,
        hash: r.hash || undefined,
      }));

      // Update source of truth for current view
      setCurrentReceiptsList(bucketReceipts);

      // Update cache
      setReceipts(prev => {
        const updated = { ...prev };
        for (const receipt of bucketReceipts) {
          updated[receipt.id] = receipt;
        }
        return updated;
      });

      return bucketReceipts;
    } catch (error) {
      console.error('Failed to load receipts for bucket:', error);
      return [];
    }
  }, []);

  const getUnallocatedReceipts = useCallback(async (): Promise<Receipt[]> => {
    // Dashboard handles the refresh which populates unallocatedReceipts
    return unallocatedReceipts;
  }, [unallocatedReceipts]);

  return (
    <TaxosContext.Provider value={{
      buckets,
      bucketSummaries,
      unallocatedSummary,
      receipts,
      unallocatedReceipts,
      currentReceiptsList,
      loading,
      authenticated,
      isNameTaken,
      addBucket,
      updateBucket,
      deleteBucket,
      addReceipt,
      updateReceipt,
      deleteReceipt,
      refreshBuckets,
      loadReceiptsForBucket,
      getUnallocatedReceipts,
    }}>
      {children}
    </TaxosContext.Provider>
  );
};

export const useTaxos = () => {
  const context = useContext(TaxosContext);
  if (context === undefined) {
    throw new Error('useTaxos must be used within a TaxosProvider');
  }
  return context;
};
