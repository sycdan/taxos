import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Database, TrendingUp, ChevronRight, Eye, EyeOff, Plus, X } from 'lucide-react';
import { UNALLOCATED_BUCKET_ID } from '../types';
import { useTaxos } from '../contexts/TaxosContext';

interface DashboardProps {
  onSelectBucket: (bucketId: string) => void;
  onUpload: (file: File) => void;
  showEmpty: boolean;
  setShowEmpty: (show: boolean) => void;
  startDate: Date;
  endDate: Date;
  onAddBucket: (name: string) => void;
  isNameTaken: (name: string) => boolean;
}

const Dashboard: React.FC<DashboardProps> = ({
  onSelectBucket,
  onUpload,
  showEmpty,
  setShowEmpty,
  startDate,
  endDate,
  onAddBucket,
  isNameTaken
}) => {
  const { bucketSummaries, refreshBuckets } = useTaxos();
  const [isDragging, setIsDragging] = React.useState(false);
  const [isAddingBucket, setIsAddingBucket] = React.useState(false);
  const [newBucketName, setNewBucketName] = React.useState('');
  const dragCounter = React.useRef(0);

  // Refresh buckets when date range changes
  React.useEffect(() => {
    void refreshBuckets(startDate, endDate);
  }, [startDate, endDate, refreshBuckets]);

  React.useEffect(() => {
    const handleWindowDragOver = (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
    };

    const handleWindowDrop = (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
    };

    window.addEventListener('dragover', handleWindowDragOver);
    window.addEventListener('drop', handleWindowDrop);

    return () => {
      window.removeEventListener('dragover', handleWindowDragOver);
      window.removeEventListener('drop', handleWindowDrop);
    };
  }, []);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current--;
    if (dragCounter.current === 0) {
      setIsDragging(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    e.dataTransfer.dropEffect = 'copy';
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounter.current = 0;

    const files = Array.from(e.dataTransfer.files);
    files.forEach(file => {
      onUpload(file);
    });
  };



  const handleCreateBucket = (e: React.FormEvent) => {
    e.preventDefault();
    if (newBucketName.trim() && !isNameTaken(newBucketName.trim())) {
      onAddBucket(newBucketName.trim());
      setNewBucketName('');
      setIsAddingBucket(false);
    }
  };

  const bucketTotals = useMemo(() => {
    // Add unallocated as a pseudo-bucket (summaries from API don't include it)
    return [
      ...bucketSummaries.map(summary => ({
        id: summary.bucket.id,
        name: summary.bucket.name,
        total: summary.totalAmount,
        count: summary.receiptCount
      })),
      // Unallocated bucket - will be populated via API when clicked
      { id: UNALLOCATED_BUCKET_ID, name: 'Unallocated', total: 0, count: 0 }
    ];
  }, [bucketSummaries]);

  const filteredBuckets = useMemo(() => {
    if (showEmpty) return bucketTotals;
    return bucketTotals.filter(b => b.total > 0 || b.id === UNALLOCATED_BUCKET_ID);
  }, [bucketTotals, showEmpty]);

  const totalFunds = useMemo(() => {
    return bucketTotals.reduce((sum, b) => sum + b.total, 0);
  }, [bucketTotals]);

  const totalAllocated = useMemo(() => {
    return bucketTotals
      .filter(b => b.id !== UNALLOCATED_BUCKET_ID)
      .reduce((sum, b) => sum + b.total, 0);
  }, [bucketTotals]);

  return (
    <div
      className="dashboard-outer"
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      style={{ position: 'relative', minHeight: 'calc(100vh - 120px)' }}
    >
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="dashboard"
      >
        <div className="flex justify-end items-center mb-8">
          <div className="card flex items-center gap-4 py-3">
            <TrendingUp className="text-primary" size={24} />
            <div>
              <div className="text-xs text-muted uppercase font-bold">Total Allocated</div>
              <div className="text-2xl font-bold">${totalAllocated.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            </div>
          </div>
        </div>

        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl">Spending Buckets</h2>
          <div className="flex items-center gap-2">
            <button
              className="btn btn-primary btn-sm flex items-center gap-1"
              onClick={() => setIsAddingBucket(true)}
            >
              <Plus size={16} />
              <span>New Bucket</span>
            </button>
            <button
              className="btn btn-ghost btn-sm flex items-center gap-2"
              onClick={() => setShowEmpty(!showEmpty)}
            >
              {showEmpty ? <EyeOff size={16} /> : <Eye size={16} />}
              {showEmpty ? 'Hide Empty' : 'Show Empty'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
          {filteredBuckets.map((bucket, index) => (
            <motion.div
              key={bucket.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.05 }}
              className="card cursor-pointer group"
              onClick={() => onSelectBucket(bucket.id)}
            >
              <div className="flex justify-between items-start mb-4">
                <div className="p-2 bg-primary/10 rounded-lg text-primary">
                  <Database size={20} />
                </div>
                <ChevronRight className="text-muted group-hover:text-primary transition-colors" size={20} />
              </div>
              <div className="text-muted text-sm uppercase font-semibold mb-1">{bucket.name}</div>
              <div className="flex items-baseline gap-2">
                <div className="text-3xl font-bold">${bucket.total.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                <div className="text-muted text-sm font-bold">({bucket.count})</div>
              </div>

              <div className="mt-4 w-full bg-slate-800 rounded-full h-1.5 overflow-hidden" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <div
                  className="h-full bg-primary"
                  style={{
                    width: `${totalFunds > 0 ? (bucket.total / totalFunds * 100) : 0}%`,
                    transition: 'width 1s ease-out'
                  }}
                />
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      <AnimatePresence>
        {isDragging && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-primary/10 backdrop-blur-md border-4 border-dashed border-primary flex items-center justify-center m-4 rounded-3xl"
            style={{ pointerEvents: 'none' }}
          >
            <div className="text-center">
              <div className="p-6 bg-primary/20 rounded-full inline-block mb-4">
                <TrendingUp size={64} className="text-primary animate-bounce" />
              </div>
              <h2 className="text-4xl font-black text-white">Drop to Upload Receipt</h2>
              <p className="text-xl text-primary font-bold mt-2">Release files anywhere to start allocating</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {isAddingBucket && (
        <div className="fixed inset-0 bg-black-60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card w-full max-w-md relative"
            style={{ border: '1px solid rgba(255,255,255,0.1)' }}
          >
            <button
              className="absolute top-4 right-4 text-muted hover:text-white"
              onClick={() => setIsAddingBucket(false)}
            >
              <X size={20} />
            </button>
            <h2 className="text-2xl font-bold mb-2">Create New Bucket</h2>
            <p className="text-muted mb-6">Give your new category a descriptive name.</p>

            <form onSubmit={handleCreateBucket}>
              <div className="mb-6">
                <input
                  autoFocus
                  type="text"
                  placeholder="e.g. Travel, Office Supplies"
                  className={`w-full text-lg ${newBucketName.trim() && isNameTaken(newBucketName) ? 'border-error' : ''}`}
                  value={newBucketName}
                  onChange={(e) => setNewBucketName(e.target.value)}
                />
                {newBucketName.trim() && isNameTaken(newBucketName) && (
                  <div className="text-error text-xs font-semibold mt-2">This bucket name is already taken.</div>
                )}
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  className="btn btn-ghost flex-1"
                  onClick={() => setIsAddingBucket(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary flex-1"
                  disabled={!newBucketName.trim() || isNameTaken(newBucketName)}
                >
                  Create Bucket
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
