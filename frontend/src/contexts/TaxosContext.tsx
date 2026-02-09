import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Timestamp } from '@bufbuild/protobuf';
import type { Bucket, Receipt } from '../types';
import { UNALLOCATED_BUCKET_ID } from '../types';
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
  receipts: Receipt[];
  loading: boolean;
  authenticated: boolean;
  isNameTaken: (name: string, excludeId?: string) => boolean;
  addBucket: (name: string) => Promise<boolean>;
  updateBucket: (id: string, name: string) => Promise<boolean>;
  deleteBucket: (id: string) => Promise<void>;
  addReceipt: (receipt: Omit<Receipt, 'id'>) => void;
  updateReceipt: (receipt: Receipt) => void;
  deleteReceipt: (id: string) => void;
  getBucketTotal: (bucketId: string, startDate?: Date, endDate?: Date) => number;
  getBucketCount: (bucketId: string, startDate?: Date, endDate?: Date) => number;
  refreshBuckets: () => Promise<void>;
  getUnallocatedReceipts: (startDate: Date, endDate: Date) => Promise<Receipt[]>;
}

const TaxosContext = createContext<TaxosContextType | undefined>(undefined);

export const TaxosProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [buckets, setBuckets] = useState<Bucket[]>([]);
  const [receipts, setReceipts] = useState<Receipt[]>(() => {
    // Keep receipts in localStorage for now until we implement receipt API
    const saved = localStorage.getItem('taxos_receipts');
    return saved ? JSON.parse(saved) : [];
  });
  const [loading, setLoading] = useState(true);
  const [authenticated] = useState(!!getToken());

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

  const refreshBuckets = async () => {
    try {
      setLoading(true);
      if (!authenticated) {
        setLoading(false);
        return;
      }
      const response = await client.listBuckets({});
      const apiBuckets: Bucket[] = response.buckets.map(bucketSummary => ({
        id: bucketSummary.bucket!.guid,
        name: bucketSummary.bucket!.name
      }));
      setBuckets(apiBuckets);
    } catch (error) {
      console.error('Failed to load buckets:', error);
      // Fallback to localStorage on error
      const saved = localStorage.getItem('taxos_buckets');
      setBuckets(saved ? JSON.parse(saved) : []);
    } finally {
      setLoading(false);
    }
  };

  // Load buckets on mount if authenticated
  useEffect(() => {
    if (authenticated) {
      refreshBuckets();
    } else {
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
      setReceipts(prev => prev.map(r => ({
        ...r,
        allocations: r.allocations.filter(a => a.bucketId !== id)
      })));
    } catch (error) {
      console.error('Failed to delete bucket:', error);
      // Fallback to local deletion
      setBuckets(prev => prev.filter(b => b.id !== id));
      setReceipts(prev => prev.map(r => ({
        ...r,
        allocations: r.allocations.filter(a => a.bucketId !== id)
      })));
    }
  };

  const addReceipt = (receipt: Omit<Receipt, 'id'>) => {
    const createLocal = (fallbackReceipt: Omit<Receipt, 'id'>) => {
      setReceipts(prev => {
        if (fallbackReceipt.hash && prev.some(r => r.hash === fallbackReceipt.hash)) {
          console.warn('Duplicate receipt detected, skipping:', fallbackReceipt.vendor);
          return prev;
        }
        const newReceipt = { ...fallbackReceipt, id: uuidv4() };
        return [...prev, newReceipt];
      });
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
            bucketGuid: a.bucketId,
            amount: a.amount,
          })),
          ref: receipt.ref || '',
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
            bucketId: a.bucketGuid,
            amount: a.amount,
          })),
          ref: response.ref || undefined,
          notes: response.notes || undefined,
          file: response.file || undefined,
          hash: response.hash || undefined,
        };

        setReceipts(prev => {
          if (createdReceipt.hash && prev.some(r => r.hash === createdReceipt.hash)) {
            console.warn('Duplicate receipt detected, skipping:', createdReceipt.vendor);
            return prev;
          }
          return [...prev, createdReceipt];
        });
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
    setReceipts(prev => prev.map(r => r.id === receipt.id ? receipt : r));

    try {
      const response = await client.updateReceipt({
        guid: receipt.id,
        vendor: receipt.vendor,
        total: receipt.total,
        date: toTimestamp(receipt.date),
        timezone: receipt.timezone,
        allocations: receipt.allocations.map(a => ({
          bucketGuid: a.bucketId,
          amount: a.amount,
        })),
        ref: receipt.ref || '',
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
          bucketId: a.bucketGuid,
          amount: a.amount,
        })),
        ref: response.ref || '',
        notes: response.notes || '',
        hash: response.hash || '',
      };

      setReceipts(prev => prev.map(r => r.id === updatedReceipt.id ? updatedReceipt : r));
    } catch (error) {
      console.error('Failed to update receipt:', error);
      // Already updated local state optimistically
    }
  };

  const deleteReceipt = async (id: string) => {
    try {
      await client.deleteReceipt({ guid: id });
      setReceipts(prev => prev.filter(r => r.id !== id));
    } catch (error) {
      console.error('Failed to delete receipt:', error);
      // Fallback to local deletion
      setReceipts(prev => prev.filter(r => r.id !== id));
    }
  };

  const getBucketTotal = (bucketId: string, startDate?: Date, endDate?: Date) => {
    return receipts
      .filter(r => {
        const rDate = new Date(r.date);
        if (startDate && rDate < startDate) return false;
        if (endDate && rDate > endDate) return false;
        return true;
      })
      .reduce((sum, r) => {
        const alloc = r.allocations.find(a => a.bucketId === bucketId);
        if (alloc) return sum + alloc.amount;

        if (bucketId === UNALLOCATED_BUCKET_ID) {
          const allocatedSum = r.allocations.reduce((s, a) => s + a.amount, 0);
          return sum + (r.total - allocatedSum);
        }

        return sum;
      }, 0);
  };

  const getBucketCount = (bucketId: string, startDate?: Date, endDate?: Date) => {
    return receipts
      .filter(r => {
        const rDate = new Date(r.date);
        if (startDate && rDate < startDate) return false;
        if (endDate && rDate > endDate) return false;

        const hasAlloc = r.allocations.some(a => a.bucketId === bucketId);
        if (hasAlloc) return true;

        if (bucketId === UNALLOCATED_BUCKET_ID) {
          const allocatedSum = r.allocations.reduce((s, a) => s + a.amount, 0);
          // Unallocated if sum < total OR if it's a new $0 receipt with no allocations
          return allocatedSum < r.total || (r.total === 0 && r.allocations.length === 0);
        }

        return false;
      }).length;
  };

  const getUnallocatedReceipts = async (startDate: Date, endDate: Date): Promise<Receipt[]> => {
    try {
      const response = await client.listUnallocatedReceipts({
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
          bucketId: a.bucketGuid,
          amount: a.amount,
        })),
        ref: r.ref || undefined,
        notes: r.notes || undefined,
        file: r.file || undefined,
        hash: r.hash || undefined,
      }));

      return unallocatedReceipts;
    } catch (error) {
      console.error('Failed to load unallocated receipts:', error);
      // Fallback to client-side filtering
      return receipts.filter(r => {
        const rDate = new Date(r.date);
        if (rDate < startDate || rDate > endDate) return false;
        const totalAllocated = r.allocations.reduce((sum, a) => sum + a.amount, 0);
        return totalAllocated < r.total || (r.total === 0 && r.allocations.length === 0);
      }).sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    }
  };

  return (
    <TaxosContext.Provider value={{
      buckets,
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
      getBucketTotal,
      getBucketCount,
      refreshBuckets,
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
