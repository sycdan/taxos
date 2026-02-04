import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { v4 as uuidv4 } from 'uuid';
import type { Bucket, Receipt } from '../types';
import { UNALLOCATED_BUCKET_ID } from '../types';
import { client } from '../api/client';

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

  // Keep receipts in localStorage in sync
  useEffect(() => {
    localStorage.setItem('taxos_receipts', JSON.stringify(receipts));
  }, [receipts]);

  const refreshBuckets = async () => {
    try {
      setLoading(true);
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

  // Load buckets on mount
  useEffect(() => {
    refreshBuckets();
  }, []);

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
    setReceipts(prev => {
      // Prevent duplicates if hash is provided
      if (receipt.hash && prev.some(r => r.hash === receipt.hash)) {
        console.warn('Duplicate receipt detected, skipping:', receipt.vendor);
        return prev;
      }
      const newReceipt = { ...receipt, id: uuidv4() };
      return [...prev, newReceipt];
    });
  };

  const updateReceipt = (receipt: Receipt) => {
    setReceipts(prev => prev.map(r => r.id === receipt.id ? receipt : r));
  };

  const deleteReceipt = (id: string) => {
    setReceipts(prev => prev.filter(r => r.id !== id));
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

  return (
    <TaxosContext.Provider value={{
      buckets,
      receipts,
      loading,
      isNameTaken,
      addBucket,
      updateBucket,
      deleteBucket,
      addReceipt,
      updateReceipt,
      deleteReceipt,
      getBucketTotal,
      getBucketCount,
      refreshBuckets
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
