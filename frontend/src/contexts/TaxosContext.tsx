import React, { createContext, useContext, useState, useEffect, useCallback, useMemo, type ReactNode } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Timestamp } from '@bufbuild/protobuf';
import type { Bucket, BucketSummary, Receipt } from '../types';
import { client, getToken, dateToTimestamp } from '../api/client';

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
  loading: boolean;
  authenticated: boolean;
  isNameTaken: (name: string, excludeId?: string) => boolean;
  addBucket: (name: string) => Promise<boolean>;
  updateBucket: (id: string, name: string) => Promise<boolean>;
  deleteBucket: (id: string) => Promise<void>;
  addReceipt: (receipt: Omit<Receipt, 'id'>) => void;
  updateReceipt: (receipt: Receipt) => void;
  deleteReceipt: (id: string) => void;
  refreshBuckets: (startDate?: Date, endDate?: Date) => Promise<void>;
  loadReceiptsForBucket: (bucketId: string, startDate: Date, endDate: Date) => Promise<Receipt[]>;
  getUnallocatedReceipts: (startDate: Date, endDate: Date) => Promise<Receipt[]>;
}

const TaxosContext = createContext<TaxosContextType | undefined>(undefined);

export const TaxosProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [buckets, setBuckets] = useState<Bucket[]>([]);
  const [bucketSummaries, setBucketSummaries] = useState<BucketSummary[]>([]);
  const [unallocatedSummary, setUnallocatedSummary] = useState<{ totalAmount: number; receiptCount: number }>(() => {
    const saved = localStorage.getItem('taxos_unallocated_summary');
    return saved ? JSON.parse(saved) : { totalAmount: 0, receiptCount: 0 };
  });
  const [receipts, setReceipts] = useState<Record<string, Receipt>>(() => {
    // Load receipts from localStorage as guid-indexed dict
    const saved = localStorage.getItem('taxos_receipts');
    return saved ? JSON.parse(saved) : {};
  });
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

  // Keep receipts in localStorage in sync
  useEffect(() => {
    localStorage.setItem('taxos_receipts', JSON.stringify(receipts));
  }, [receipts]);

  // Keep unallocated summary in localStorage in sync
  useEffect(() => {
    localStorage.setItem('taxos_unallocated_summary', JSON.stringify(unallocatedSummary));
  }, [unallocatedSummary]);

  const refreshBuckets = useCallback(async (startDate?: Date, endDate?: Date) => {
    // Only refresh if dates have actually changed or it's the initial load
    const sameStart = (!startDate && !currentDateFilter.start) || (startDate && currentDateFilter.start && startDate.getTime() === currentDateFilter.start.getTime());
    const sameEnd = (!endDate && !currentDateFilter.end) || (endDate && currentDateFilter.end && endDate.getTime() === currentDateFilter.end.getTime());

    if (sameStart && sameEnd && buckets.length > 0) {
      console.log('Skipping ListBuckets - same date filter and buckets already loaded');
      return;
    }

    try {
      setLoading(true);
      if (!authenticated) {
        setLoading(false);
        return;
      }

      console.log('Making ListBuckets request with date filter change...');
      setCurrentDateFilter({ start: startDate, end: endDate });

      const response = await client.listBuckets({
        startDate: startDate ? dateToTimestamp(startDate) as any : undefined,
        endDate: endDate ? dateToTimestamp(endDate) as any : undefined,
      });

      const apiBuckets: Bucket[] = response.buckets.map(summary => ({
        id: summary.bucket!.guid,
        name: summary.bucket!.name
      }));

      const apiSummaries: BucketSummary[] = response.buckets.map(summary => ({
        bucket: {
          id: summary.bucket!.guid,
          name: summary.bucket!.name
        },
        totalAmount: summary.totalAmount,
        receiptCount: summary.receiptCount
      }));

      setBuckets(apiBuckets);
      setBucketSummaries(apiSummaries);

      // Fetch unallocated summary with the same date filter
      try {
        const unallocatedResponse = await client.listReceipts({
          // No bucket_guid = unallocated receipts
          startDate: startDate ? dateToTimestamp(startDate) as any : undefined,
          endDate: endDate ? dateToTimestamp(endDate) as any : undefined,
        });

        // Calculate unallocated amount (total - sum of allocations)
        let totalAmount = 0;
        let receiptCount = 0;

        for (const r of unallocatedResponse.receipts) {
          const allocatedAmount = r.allocations.reduce((sum, a) => sum + a.amount, 0);
          const unallocatedAmount = r.total - allocatedAmount;
          if (unallocatedAmount > 0) {
            totalAmount += unallocatedAmount;
            receiptCount++;
          }
        }

        setUnallocatedSummary({ totalAmount, receiptCount });
      } catch (error) {
        console.error('Failed to load unallocated summary:', error);
        // Keep existing cached value on error
      }
    } catch (error) {
      console.error('Failed to load buckets:', error);
      // Don't immediately retry on error - just use fallback
      const saved = localStorage.getItem('taxos_buckets');
      setBuckets(saved ? JSON.parse(saved) : []);
      setBucketSummaries([]);
    } finally {
      setLoading(false);
    }
  }, [authenticated, currentDateFilter, buckets.length]); // Include currentDateFilter and buckets.length

  // Don't load buckets on mount - let Dashboard call refreshBuckets with date filter
  useEffect(() => {
    if (!authenticated) {
      setLoading(false);
    } else {
      // Load from localStorage on mount
      const saved = localStorage.getItem('taxos_buckets');
      if (saved) {
        setBuckets(JSON.parse(saved));
      }
      setLoading(false);
    }
  }, [authenticated]);

  // Keep localStorage as backup
  useEffect(() => {
    localStorage.setItem('taxos_buckets', JSON.stringify(buckets));
  }, [buckets]);

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
      return true;
    } catch (error) {
      console.error('Failed to create bucket:', error);
      // Fallback to local creation
      const newBucket = { id: uuidv4(), name };
      setBuckets(prev => [...prev, newBucket]);
      return true;
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
      // Fallback to local update
      setBuckets(prev => prev.map(b => b.id === id ? { ...b, name } : b));
      return true;
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
      // Fallback to local deletion
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
    }
  };

  const addReceipt = (receipt: Omit<Receipt, 'id'>) => {
    const createLocal = (fallbackReceipt: Omit<Receipt, 'id'>) => {
      if (fallbackReceipt.hash && receiptHashes.has(fallbackReceipt.hash)) {
        console.warn('Duplicate receipt detected, skipping:', fallbackReceipt.vendor);
        return;
      }
      const newReceipt = { ...fallbackReceipt, id: uuidv4() };
      setReceipts(prev => ({ ...prev, [newReceipt.id]: newReceipt }));
    };

    const toTimestamp = (iso: string) => {
      const date = new Date(iso);
      const seconds = BigInt(Math.floor(date.getTime() / 1000));
      const nanos = (date.getTime() % 1000) * 1_000_000;
      return new Timestamp({ seconds, nanos });
    };

    const timestampToIso = (ts?: Timestamp) => {
      if (!ts) return new Date().toISOString();
      const asAny = ts as any;
      if (typeof asAny.toDate === 'function') return asAny.toDate().toISOString();
      const seconds = Number(asAny.seconds ?? 0);
      const nanos = Number(asAny.nanos ?? 0);
      return new Date(seconds * 1000 + nanos / 1_000_000).toISOString();
    };

    const createRemote = async () => {
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
      } catch (error) {
        console.error('Failed to create receipt:', error);
        createLocal(receipt);
      }
    };

    void createRemote();
  };

  const updateReceipt = async (receipt: Receipt) => {
    const toTimestamp = (iso: string) => {
      const date = new Date(iso);
      const seconds = BigInt(Math.floor(date.getTime() / 1000));
      const nanos = (date.getTime() % 1000) * 1_000_000;
      return new Timestamp({ seconds, nanos });
    };

    const timestampToIso = (ts?: Timestamp) => {
      if (!ts) return new Date().toISOString();
      const asAny = ts as any;
      if (typeof asAny.toDate === 'function') return asAny.toDate().toISOString();
      const seconds = Number(asAny.seconds ?? 0);
      const nanos = Number(asAny.nanos ?? 0);
      return new Date(seconds * 1000 + nanos / 1_000_000).toISOString();
    };

    // Optimistically update local state
    setReceipts(prev => ({ ...prev, [receipt.id]: receipt }));

    try {
      const response = await client.updateReceipt({
        guid: receipt.id,
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
    } catch (error) {
      console.error('Failed to update receipt:', error);
      // Already updated local state optimistically
    }
  };

  const deleteReceipt = async (id: string) => {
    try {
      await client.deleteReceipt({ guid: id });
      setReceipts(prev => {
        const { [id]: _, ...rest } = prev;
        return rest;
      });
    } catch (error) {
      console.error('Failed to delete receipt:', error);
      // Fallback to local deletion
      setReceipts(prev => {
        const { [id]: _, ...rest } = prev;
        return rest;
      });
    }
  };

  const loadReceiptsForBucket = useCallback(async (bucketId: string, startDate: Date, endDate: Date): Promise<Receipt[]> => {
    try {
      const response = await client.listReceipts({
        bucket: bucketId,
        startDate: dateToTimestamp(startDate) as any,
        endDate: dateToTimestamp(endDate) as any,
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

      // Update localStorage cache
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
      // Fallback to client-side filtering from cache
      return Object.values(receipts).filter(r => {
        const rDate = new Date(r.date);
        if (rDate < startDate || rDate > endDate) return false;
        return r.allocations.some(a => a.bucketId === bucketId);
      }).sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    }
  }, [receipts]);

  const getUnallocatedReceipts = useCallback(async (startDate: Date, endDate: Date): Promise<Receipt[]> => {
    try {
      // Use listReceipts without bucket_guid to get unallocated receipts
      const response = await client.listReceipts({
        // No bucket_guid parameter = unallocated receipts
        startDate: dateToTimestamp(startDate) as any,
        endDate: dateToTimestamp(endDate) as any,
      });

      const unallocatedReceipts: Receipt[] = response.receipts.map(r => ({
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

      // Update localStorage cache
      setReceipts(prev => {
        const updated = { ...prev };
        for (const receipt of unallocatedReceipts) {
          updated[receipt.id] = receipt;
        }
        return updated;
      });

      return unallocatedReceipts;
    } catch (error) {
      console.error('Failed to load unallocated receipts:', error);
      // Fallback to client-side filtering
      return Object.values(receipts).filter(r => {
        const rDate = new Date(r.date);
        if (rDate < startDate || rDate > endDate) return false;
        const totalAllocated = r.allocations.reduce((sum, a) => sum + a.amount, 0);
        return totalAllocated < r.total || (r.total === 0 && r.allocations.length === 0);
      }).sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    }
  }, [receipts]);

  return (
    <TaxosContext.Provider value={{
      buckets,
      bucketSummaries,
      unallocatedSummary,
      receipts,
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
