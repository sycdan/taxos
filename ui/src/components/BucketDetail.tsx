import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Receipt as ReceiptIcon, Calendar, Hash, Edit2, Trash2, Check, X } from 'lucide-react';
import type { Bucket, Receipt } from '../types';
import { UNALLOCATED_BUCKET_ID } from '../types';
import { format } from 'date-fns';

interface BucketDetailProps {
  bucketId: string;
  buckets: Bucket[];
  receipts: Receipt[];
  onBack: () => void;
  startDate: Date;
  endDate: Date;
  onUpdateBucket: (id: string, name: string) => void;
  onDeleteBucket: (id: string) => void;
  onEditReceipt: (receipt: Receipt) => void;
  isNameTaken: (name: string, excludeId?: string) => boolean;
}

const BucketDetail: React.FC<BucketDetailProps> = ({
  bucketId,
  buckets,
  receipts,
  onBack,
  startDate,
  endDate,
  onUpdateBucket,
  onDeleteBucket,
  onEditReceipt,
  isNameTaken
}) => {
  const [isEditing, setIsEditing] = React.useState(false);
  const [editName, setEditName] = React.useState('');
  const bucketName = useMemo(() => {
    if (bucketId === UNALLOCATED_BUCKET_ID) return 'Unallocated';
    return buckets.find(b => b.id === bucketId)?.name || 'Unknown Bucket';
  }, [bucketId, buckets]);

  const handleStartEdit = () => {
    setEditName(bucketName);
    setIsEditing(true);
  };

  const handleSaveEdit = () => {
    if (editName.trim() && !isNameTaken(editName.trim(), bucketId)) {
      onUpdateBucket(bucketId, editName.trim());
      setIsEditing(false);
    }
  };

  const handleDelete = () => {
    if (window.confirm(`Are you sure you want to delete the bucket "${bucketName}"? This will not delete the receipts, but they will become unallocated.`)) {
      onDeleteBucket(bucketId);
    }
  };

  const filteredReceipts = useMemo(() => {
    return receipts.filter(r => {
      const rDate = new Date(r.date);
      if (rDate < startDate || rDate > endDate) return false;
      
      const hasAlloc = r.allocations.some(a => a.bucketId === bucketId);
      if (hasAlloc) return true;
      
      // If unallocated bucket, check if there's a remainder or it's empty
      if (bucketId === UNALLOCATED_BUCKET_ID) {
        const totalAllocated = r.allocations.reduce((sum, a) => sum + a.amount, 0);
        return totalAllocated < r.total || (r.total === 0 && r.allocations.length === 0);
      }
      
      return false;
    }).sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [receipts, bucketId, startDate, endDate]);

  const bucketTotal = useMemo(() => {
    return filteredReceipts.reduce((sum, r) => {
      const alloc = r.allocations.find(a => a.bucketId === bucketId);
      if (alloc) return sum + alloc.amount;
      if (bucketId === UNALLOCATED_BUCKET_ID) {
        const allocated = r.allocations.reduce((s, a) => s + a.amount, 0);
        return sum + (r.total - allocated);
      }
      return sum;
    }, 0);
  }, [filteredReceipts, bucketId]);

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="bucket-detail"
    >
      <button className="btn btn-ghost mb-6 group" onClick={onBack}>
        <ArrowLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
        Back to Dashboard
      </button>

      <div className="flex justify-between items-end mb-8">
        <div className="flex-1">
          {isEditing ? (
            <div className="flex flex-col gap-2 max-w-md">
              <div className="flex gap-2">
                <input 
                  autoFocus
                  className={`text-3xl font-bold bg-transparent border-b-2 border-primary focus:outline-none w-full ${editName.trim() && isNameTaken(editName, bucketId) ? 'border-error' : ''}`}
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSaveEdit()}
                />
                <button className="btn btn-ghost p-2 text-primary" onClick={handleSaveEdit} disabled={!editName.trim() || isNameTaken(editName, bucketId)}>
                  <Check size={24} />
                </button>
                <button className="btn btn-ghost p-2 text-muted" onClick={() => setIsEditing(false)}>
                  <X size={24} />
                </button>
              </div>
              {editName.trim() && isNameTaken(editName, bucketId) && (
                <div className="text-error text-xs font-semibold">Name already taken</div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-4 group/header">
              <h1 className="text-3xl font-bold">{bucketName}</h1>
              {bucketId !== UNALLOCATED_BUCKET_ID && (
                <div className="flex gap-2 opacity-0 group-hover/header:opacity-100 transition-opacity">
                  <button 
                    className="p-1.5 text-muted hover:text-primary transition-colors"
                    onClick={handleStartEdit}
                    title="Rename Bucket"
                  >
                    <Edit2 size={18} />
                  </button>
                  <button 
                    className="p-1.5 text-muted hover:text-error transition-colors"
                    onClick={handleDelete}
                    title="Delete Bucket"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              )}
            </div>
          )}
          <p className="text-muted mt-2">Transaction history for this period.</p>
        </div>
        <div className="text-right">
          <div className="text-xs text-muted uppercase font-bold">Bucket Total</div>
          <div className="text-4xl font-bold text-primary">${bucketTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        </div>
      </div>

      <div className="space-y-4" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {filteredReceipts.length === 0 ? (
          <div className="card text-center py-20 border-dashed">
            <ReceiptIcon size={48} className="mx-auto text-muted mb-4 opacity-20" />
            <p className="text-muted">No receipts found for this period.</p>
          </div>
        ) : (
          filteredReceipts.map(receipt => {
            const amountForThisBucket = bucketId === UNALLOCATED_BUCKET_ID 
              ? receipt.total - receipt.allocations.reduce((sum, a) => sum + a.amount, 0)
              : receipt.allocations.find(a => a.bucketId === bucketId)?.amount || 0;

            return (
              <motion.div 
                key={receipt.id} 
                className="card flex justify-between items-center hover:bg-slate-800/50 cursor-pointer"
                whileHover={{ x: 4 }}
                onClick={() => onEditReceipt(receipt)}
              >
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-slate-900 rounded-xl text-primary">
                    <ReceiptIcon size={24} />
                  </div>
                  <div>
                    <div className="font-bold text-lg">{receipt.vendor}</div>
                    <div className="flex items-center gap-3 text-xs text-muted mt-1">
                      <span className="flex items-center gap-1"><Calendar size={12} /> {format(new Date(receipt.date), 'MMM d, h:mm a')}</span>
                      {receipt.ref && <span className="flex items-center gap-1"><Hash size={12} /> {receipt.ref}</span>}
                    </div>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-xl font-bold">${amountForThisBucket.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                  <div className="text-xs text-muted">Total: ${receipt.total.toFixed(2)}</div>
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </motion.div>
  );
};

export default BucketDetail;
