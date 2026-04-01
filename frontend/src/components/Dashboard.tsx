import React, { useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
	Database,
	ChevronRight,
	Eye,
	EyeOff,
	Plus,
	TrendingUp,
	X,
	AlertTriangle,
} from "lucide-react";
import { useTaxos } from "../contexts/TaxosContext";

interface DashboardProps {
	viewMode: "buckets" | "vendors";
	onSelectBucket: (bucketId: string) => void;
	onSelectVendor: (vendorId: string) => void;
	onSelectUnallocated: () => void;
	onUpload: (file: File) => void;
	showEmpty: boolean;
	setShowEmpty: (show: boolean) => void;
	startDate: Date;
	endDate: Date;
	onAddBucket: (name: string) => Promise<boolean>;
	isNameTaken: (name: string) => boolean;
}

const Dashboard: React.FC<DashboardProps> = ({
	viewMode,
	onSelectBucket,
	onSelectVendor,
	onSelectUnallocated,
	onUpload,
	showEmpty,
	setShowEmpty,
	startDate,
	endDate,
	onAddBucket,
	isNameTaken,
}) => {
	const isGuid = (value: string) => /^[0-9a-f]{32}$/i.test(value);
	const { bucketSummaries, vendorSummaries, unallocatedSummary, refreshBuckets } =
		useTaxos();
	const [isDragging, setIsDragging] = React.useState(false);
	const [isAddingBucket, setIsAddingBucket] = React.useState(false);
	const [newBucketName, setNewBucketName] = React.useState("");
	const dragCounter = React.useRef(0);

	// Trigger data load on mount and whenever the date filter changes.
	// refreshBuckets loads buckets+vendors once, then only reloads receipts
	// on subsequent calls.
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
		window.addEventListener("dragover", handleWindowDragOver);
		window.addEventListener("drop", handleWindowDrop);
		return () => {
			window.removeEventListener("dragover", handleWindowDragOver);
			window.removeEventListener("drop", handleWindowDrop);
		};
	}, []);

	const handleDragEnter = (e: React.DragEvent) => {
		e.preventDefault();
		e.stopPropagation();
		dragCounter.current += 1;
		if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
			setIsDragging(true);
		}
	};

	const handleDragLeave = (e: React.DragEvent) => {
		e.preventDefault();
		e.stopPropagation();
		dragCounter.current -= 1;
		if (dragCounter.current === 0) {
			setIsDragging(false);
		}
	};

	const handleDragOver = (e: React.DragEvent) => {
		e.preventDefault();
		e.stopPropagation();
		e.dataTransfer.dropEffect = "copy";
	};

	const handleDrop = (e: React.DragEvent) => {
		e.preventDefault();
		e.stopPropagation();
		setIsDragging(false);
		dragCounter.current = 0;
		const files = Array.from(e.dataTransfer.files);
		files.forEach((file) => onUpload(file));
	};

	const handleCreateBucket = async (e: React.FormEvent) => {
		e.preventDefault();
		if (newBucketName.trim() && !isNameTaken(newBucketName.trim())) {
			await onAddBucket(newBucketName.trim());
			setNewBucketName("");
			setIsAddingBucket(false);
		}
	};

	const bucketTotals = useMemo(() => {
		return bucketSummaries.map((summary) => ({
			id: summary.bucket.id,
			name: summary.bucket.name,
			total: summary.totalAmount,
			count: summary.receiptCount,
		}));
	}, [bucketSummaries]);

	const vendorTotals = useMemo(() => {
		return vendorSummaries.map((summary) => ({
			id: summary.vendor.id,
			name: summary.vendor.name,
			total: summary.totalAmount,
			count: summary.receiptCount,
		}));
	}, [vendorSummaries]);

	const filteredBuckets = useMemo(() => {
		if (showEmpty) return bucketTotals;
		return bucketTotals.filter((b) => b.total > 0);
	}, [bucketTotals, showEmpty]);

	const filteredVendors = useMemo(() => {
		if (showEmpty) return vendorTotals;
		return vendorTotals.filter((v) => v.total > 0);
	}, [vendorTotals, showEmpty]);

	const handleVendorSelect = (vendorId: string) => {
		if (!isGuid(vendorId)) {
			console.warn("Skipping vendor selection with non-GUID id", { vendorId });
			return;
		}
		onSelectVendor(vendorId);
	};

	const totalFunds = useMemo(() => {
		if (viewMode === "vendors") {
			return vendorTotals.reduce((sum, v) => sum + v.total, 0);
		}
		return bucketTotals.reduce((sum, b) => sum + b.total, 0);
	}, [viewMode, vendorTotals, bucketTotals]);

	const showUnallocatedCard =
		viewMode === "buckets" &&
		(showEmpty || unallocatedSummary.receiptCount > 0);

	return (
		<div
			className="dashboard-outer"
			onDragEnter={handleDragEnter}
			onDragOver={handleDragOver}
			onDragLeave={handleDragLeave}
			onDrop={handleDrop}
			style={{ position: "relative", minHeight: "calc(100vh - 120px)" }}
		>
			<motion.div
				initial={{ opacity: 0, y: 10 }}
				animate={{ opacity: 1, y: 0 }}
				className="dashboard"
			>
				<div className="flex justify-between items-center mb-6">
					<h2 className="text-xl">
						{viewMode === "buckets" ? "Buckets" : "Vendors"}
					</h2>
					<div className="flex items-center gap-2">
						{viewMode === "buckets" && (
							<button
								className="btn btn-primary btn-sm flex items-center gap-1"
								onClick={() => setIsAddingBucket(true)}
							>
								<Plus size={16} />
								<span>Add Bucket</span>
							</button>
						)}
						<button
							className="btn btn-ghost btn-sm flex items-center gap-2"
							onClick={() => setShowEmpty(!showEmpty)}
						>
							{showEmpty ? <EyeOff size={16} /> : <Eye size={16} />}
							{showEmpty ? "Hide Empty" : "Show Empty"}
						</button>
					</div>
				</div>

				<div
					className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
					style={{
						display: "grid",
						gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
						gap: "1.5rem",
					}}
				>
					{showUnallocatedCard && (() => {
						const hasItems = unallocatedSummary.receiptCount > 0;
						return (
							<motion.div
								key="unallocated"
								initial={{ opacity: 0, scale: 0.95 }}
								animate={{ opacity: 1, scale: 1 }}
								transition={{ delay: 0 }}
								className="card cursor-pointer group"
								style={hasItems ? { border: "1px solid rgba(var(--warning-rgb, 245 158 11) / 0.3)" } : undefined}
								onClick={onSelectUnallocated}
							>
								<div className="flex justify-between items-start mb-4">
									<div className={`p-2 rounded-lg ${hasItems ? "bg-warning/10 text-warning" : "bg-primary/10 text-primary"}`}>
										{hasItems ? <AlertTriangle size={20} /> : <Database size={20} />}
									</div>
									<ChevronRight
										className={`transition-colors text-muted ${hasItems ? "group-hover:text-warning" : "group-hover:text-primary"}`}
										size={20}
									/>
								</div>
								<div className={`text-sm uppercase font-semibold mb-1 ${hasItems ? "text-warning" : "text-muted"}`}>
									Unallocated
								</div>
								<div className="flex items-baseline gap-2">
									<div className={`text-3xl font-bold ${hasItems ? "text-warning" : ""}`}>
										$
										{unallocatedSummary.totalAmount.toLocaleString(undefined, {
											minimumFractionDigits: 2,
											maximumFractionDigits: 2,
										})}
									</div>
									<div className="text-muted text-sm font-bold">
										({unallocatedSummary.receiptCount})
									</div>
								</div>
								<div
									className="mt-4 w-full rounded-full h-1.5 overflow-hidden"
									style={{ background: "rgba(255,255,255,0.05)" }}
								>
									{hasItems && (
										<div
											className="h-full bg-warning"
											style={{ width: "100%", opacity: 0.6 }}
										/>
									)}
								</div>
							</motion.div>
						);
					})()}

					{viewMode === "buckets" &&
						filteredBuckets.map((bucket, index) => (
							<motion.div
								key={bucket.id}
								initial={{ opacity: 0, scale: 0.95 }}
								animate={{ opacity: 1, scale: 1 }}
								transition={{ delay: (index + (showUnallocatedCard ? 1 : 0)) * 0.05 }}
								className="card cursor-pointer group"
								onClick={() => onSelectBucket(bucket.id)}
							>
								<div className="flex justify-between items-start mb-4">
									<div className="p-2 bg-primary/10 rounded-lg text-primary">
										<Database size={20} />
									</div>
									<ChevronRight
										className="text-muted group-hover:text-primary transition-colors"
										size={20}
									/>
								</div>
								<div className="text-muted text-sm uppercase font-semibold mb-1">
									{bucket.name}
								</div>
								<div className="flex items-baseline gap-2">
									<div className="text-3xl font-bold">
										$
										{bucket.total.toLocaleString(undefined, {
											minimumFractionDigits: 2,
											maximumFractionDigits: 2,
										})}
									</div>
									<div className="text-muted text-sm font-bold">
										({bucket.count})
									</div>
								</div>
								<div
									className="mt-4 w-full bg-slate-800 rounded-full h-1.5 overflow-hidden"
									style={{ background: "rgba(255,255,255,0.05)" }}
								>
									<div
										className="h-full bg-primary"
										style={{
											width: `${totalFunds > 0 ? (bucket.total / totalFunds) * 100 : 0}%`,
											transition: "width 1s ease-out",
										}}
									/>
								</div>
							</motion.div>
						))}

					{viewMode === "vendors" &&
						filteredVendors
							.slice()
							.sort((a, b) => a.name.localeCompare(b.name))
							.map((vendor, index) => (
								<motion.div
									key={vendor.id}
									initial={{ opacity: 0, scale: 0.95 }}
									animate={{ opacity: 1, scale: 1 }}
									transition={{ delay: index * 0.05 }}
									className="card cursor-pointer group"
									onClick={() => handleVendorSelect(vendor.id)}
								>
									<div className="flex justify-between items-start mb-4">
										<div className="p-2 bg-primary/10 rounded-lg text-primary">
											<Database size={20} />
										</div>
										<ChevronRight
											className="text-muted group-hover:text-primary transition-colors"
											size={20}
										/>
									</div>
									<div className="text-muted text-sm uppercase font-semibold mb-1">
										{vendor.name}
									</div>
									<div className="flex items-baseline gap-2">
										<div className="text-3xl font-bold">
											$
											{vendor.total.toLocaleString(undefined, {
												minimumFractionDigits: 2,
												maximumFractionDigits: 2,
											})}
										</div>
										<div className="text-muted text-sm font-bold">
											({vendor.count})
										</div>
									</div>
									<div
										className="mt-4 w-full bg-slate-800 rounded-full h-1.5 overflow-hidden"
										style={{ background: "rgba(255,255,255,0.05)" }}
									>
										<div
											className="h-full bg-primary"
											style={{
												width: `${totalFunds > 0 ? (vendor.total / totalFunds) * 100 : 0}%`,
												transition: "width 1s ease-out",
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
						style={{ pointerEvents: "none" }}
					>
						<div className="text-center">
							<div className="p-6 bg-primary/20 rounded-full inline-block mb-4">
								<TrendingUp size={64} className="text-primary animate-bounce" />
							</div>
							<h2 className="text-4xl font-black text-white">
								Drop to Upload Receipt
							</h2>
							<p className="text-xl text-primary font-bold mt-2">
								Release files anywhere to start allocating
							</p>
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
						style={{ border: "1px solid rgba(255,255,255,0.1)" }}
					>
						<button
							className="absolute top-4 right-4 text-muted hover:text-white"
							onClick={() => setIsAddingBucket(false)}
						>
							<X size={20} />
						</button>
						<h2 className="text-2xl font-bold mb-2">Create New Bucket</h2>
						<p className="text-muted mb-6">
							Give your new category a descriptive name.
						</p>
						<form onSubmit={handleCreateBucket}>
							<div className="mb-6">
								<input
									autoFocus
									type="text"
									placeholder="e.g. Travel, Office Supplies"
									className={`w-full text-lg ${newBucketName.trim() && isNameTaken(newBucketName) ? "border-error" : ""}`}
									value={newBucketName}
									onChange={(e) => setNewBucketName(e.target.value)}
								/>
								{newBucketName.trim() && isNameTaken(newBucketName) && (
									<div className="text-error text-xs font-semibold mt-2">
										This bucket name is already taken.
									</div>
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
