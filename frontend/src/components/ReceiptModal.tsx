import React, { useState, useEffect, useMemo, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
	X,
	DollarSign,
	Calendar as CalendarIcon,
	Tag,
	Plus,
	Trash2,
	Lock,
	Unlock,
	Download,
} from "lucide-react";
import type { Bucket, Receipt, ReceiptAllocation } from "../types";
import { format } from "date-fns";
import UploadProgressWidget from "./UploadProgressWidget";
import { uploadReceiptFile, downloadReceiptFile } from "../api/client";

interface ReceiptModalProps {
	isOpen: boolean;
	onClose: () => void;
	onSave: (receipt: Omit<Receipt, "id">) => void;
	onDelete: (id: string) => void;
	buckets: Bucket[];
	initialFile?: string;
	editingReceipt?: Receipt;
	// File upload props
	uploadingFile?: { file: File; hash: string }; // File being uploaded
	onFileUploadComplete?: (hash: string, filename: string) => void;
}

const SEGMENT_COLORS = [
	"#6366f1", // indigo
	"#a855f7", // purple
	"#10b981", // emerald
	"#f59e0b", // amber
	"#ec4899", // pink
	"#06b6d4", // cyan
];

const ReceiptModal: React.FC<ReceiptModalProps> = ({
	isOpen,
	onClose,
	onSave,
	onDelete,
	buckets,
	initialFile,
	editingReceipt,
	uploadingFile,
	onFileUploadComplete,
}) => {
	const [vendor, setVendor] = useState("");
	const [total, setTotal] = useState<number>(0);
	const [date, setDate] = useState(format(new Date(), "yyyy-MM-dd'T'HH:mm"));
	const [ref, setRef] = useState("");
	const [notes, setNotes] = useState("");
	const [allocations, setAllocations] = useState<ReceiptAllocation[]>([]);
	const [manualAllocations, setManualAllocations] = useState<Set<string>>(
		new Set(),
	);

	// File upload state
	const [isUploading, setIsUploading] = useState(false);
	const [uploadProgress, setUploadProgress] = useState(0);
	const [uploadedFileHash, setUploadedFileHash] = useState<string>("");
	const [uploadedFileName, setUploadedFileName] = useState<string>("");
	const [uploadError, setUploadError] = useState<string>("");

	// File download state
	const [isDownloading, setIsDownloading] = useState(false);
	const [downloadError, setDownloadError] = useState<string>("");

	const vendorRef = useRef<HTMLInputElement>(null);
	const lastUploadedHashRef = useRef<string>("");

	// Reset form when opening
	useEffect(() => {
		if (isOpen) {
			if (editingReceipt) {
				setVendor(editingReceipt.vendor);
				setTotal(editingReceipt.total);
				setDate(format(new Date(editingReceipt.date), "yyyy-MM-dd'T'HH:mm"));
				setRef(editingReceipt.ref || "");
				setNotes(editingReceipt.notes || "");
				setAllocations(editingReceipt.allocations);
				// If an allocation has a non-auto-calculated feel, we might want to track manual state,
				// but for now let's just assume they are manual if they exist and are distinct?
				// Actually, the simpler way is to just treat them as manual if they were saved that way.
				// But the ReceiptAllocation type doesn't track manual state.
				// Let's just set them all to manual when editing to prevent auto-splitter from stomping them immediately.
				setManualAllocations(
					new Set(editingReceipt.allocations.map((a) => a.bucketId)),
				);
			} else {
				setVendor("");
				setTotal(0);
				setDate(format(new Date(), "yyyy-MM-dd'T'HH:mm"));
				setRef("");
				setNotes("");
				setAllocations([]);
				setManualAllocations(new Set());
				// Reset upload state when opening fresh modal
				setUploadedFileHash("");
				setUploadedFileName("");
				setUploadError("");
				setIsUploading(false);
				setUploadProgress(0);
				lastUploadedHashRef.current = "";
			}
			setTimeout(() => vendorRef.current?.focus(), 100);
		}
	}, [isOpen, editingReceipt]);

	const allocatedTotal = useMemo(() => {
		return allocations.reduce((sum, a) => sum + a.amount, 0);
	}, [allocations]);

	const unallocatedAmount = useMemo(() => {
		return Math.max(0, total - allocatedTotal);
	}, [total, allocatedTotal]);

	const updateSplits = (
		currentAllocations: ReceiptAllocation[],
		manualIds: Set<string>,
		newTotal: number,
	) => {
		if (currentAllocations.length === 0) {
			setAllocations([]);
			return;
		}

		const manualTotal = Array.from(manualIds).reduce((sum, id) => {
			const a = currentAllocations.find((x) => x.bucketId === id);
			return sum + (a?.amount || 0);
		}, 0);

		const remainingToSplit = newTotal - manualTotal;
		const splitCount = currentAllocations.filter(
			(a) => !manualIds.has(a.bucketId),
		).length;

		let nextAllocations = [...currentAllocations];

		if (splitCount > 0 && remainingToSplit > 0) {
			const splitAmount = Number((remainingToSplit / splitCount).toFixed(2));
			let distributed = 0;
			let count = 0;

			nextAllocations = nextAllocations.map((a) => {
				if (manualIds.has(a.bucketId)) return a;

				count++;
				const isLast = count === splitCount;
				const amount = isLast
					? Number((remainingToSplit - distributed).toFixed(2))
					: splitAmount;
				distributed += amount;
				return { ...a, amount };
			});
		} else if (splitCount > 0) {
			nextAllocations = nextAllocations.map((a) =>
				manualIds.has(a.bucketId) ? a : { ...a, amount: 0 },
			);
		}
		setAllocations(nextAllocations);
	};

	const handleTotalChange = (val: number) => {
		setTotal(val);
		updateSplits(allocations, manualAllocations, val);
	};

	const handleAddBucket = (bucketId: string) => {
		if (allocations.some((a) => a.bucketId === bucketId)) return;
		const newAllocations = [...allocations, { bucketId, amount: 0 }];
		updateSplits(newAllocations, manualAllocations, total);
	};

	const handleRemoveBucket = (bucketId: string) => {
		const newAllocations = allocations.filter((a) => a.bucketId !== bucketId);
		const newManual = new Set(manualAllocations);
		newManual.delete(bucketId);
		setManualAllocations(newManual);
		updateSplits(newAllocations, newManual, total);
	};

	const handleManualAmount = (bucketId: string, amount: number) => {
		const newManual = new Set(manualAllocations);
		newManual.add(bucketId);
		setManualAllocations(newManual);

		const newAllocations = allocations.map((a) =>
			a.bucketId === bucketId ? { ...a, amount } : a,
		);
		updateSplits(newAllocations, newManual, total);
	};

	const toggleManual = (bucketId: string) => {
		const newManual = new Set(manualAllocations);
		if (newManual.has(bucketId)) {
			newManual.delete(bucketId);
		} else {
			newManual.add(bucketId);
		}
		setManualAllocations(newManual);
		updateSplits(allocations, newManual, total);
	};

	const handleDelete = () => {
		if (
			editingReceipt &&
			window.confirm("Are you sure you want to delete this receipt?")
		) {
			onDelete(editingReceipt.id);
			onClose();
		}
	};

	const handleDownload = async () => {
		const fileHash = editingReceipt?.hash;
		if (!fileHash) {
			setDownloadError("No file available for download");
			return;
		}

		setIsDownloading(true);
		setDownloadError("");

		try {
			await downloadReceiptFile(fileHash);
		} catch (error) {
			setDownloadError(error instanceof Error ? error.message : "Download failed");
		} finally {
			setIsDownloading(false);
		}
	};

	const handleSave = () => {
		onSave({
			...(editingReceipt ? { id: editingReceipt.id } : {}),
			vendor,
			total,
			date: new Date(date).toISOString(),
			timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
			allocations,
			ref: ref || undefined,
			notes: notes || undefined,
			file: uploadedFileName || initialFile || editingReceipt?.file,
			hash: uploadedFileHash || editingReceipt?.hash,
		} as any);
		onClose();
	};

	// Handle file upload when uploadingFile prop changes
	useEffect(() => {
		if (uploadingFile && isOpen && uploadingFile.hash !== lastUploadedHashRef.current) {
			const uploadFile = async () => {
				setUploadError("");
				setIsUploading(true);
				setUploadProgress(0);

				try {
					await uploadReceiptFile(uploadingFile.file, uploadingFile.hash, setUploadProgress);

					setUploadedFileHash(uploadingFile.hash);
					setUploadedFileName(uploadingFile.file.name);
					setIsUploading(false);
					lastUploadedHashRef.current = uploadingFile.hash;

					// Set initial values based on uploaded file
					if (!vendor) {
						setVendor(uploadingFile.file.name.split('.')[0] || "");
					}

					onFileUploadComplete?.(uploadingFile.hash, uploadingFile.file.name);
				} catch (error) {
					setIsUploading(false);
					setUploadProgress(0);
					setUploadError(error instanceof Error ? error.message : "Upload failed");
				}
			};

			uploadFile();
		}
	}, [uploadingFile, isOpen]);

	if (!isOpen) return null;

	const availableBuckets = buckets.filter(
		(b) => !allocations.some((a) => a.bucketId === b.id),
	);
	const isOverAllocated = allocatedTotal > total;

	return (
		<div
			className="modal-overlay"
			style={{
				position: "fixed",
				inset: 0,
				backgroundColor: "rgba(0,0,0,0.85)",
				backdropFilter: "blur(12px)",
				display: "flex",
				alignItems: "center",
				justifyContent: "center",
				zIndex: 50,
				padding: "1rem",
			}}
		>
			<motion.div
				initial={{ scale: 0.95, opacity: 0, y: 20 }}
				animate={{ scale: 1, opacity: 1, y: 0 }}
				className="card"
				style={{
					width: "100%",
					maxWidth: "640px",
					maxHeight: "95vh",
					overflowY: "auto",
					padding: "2rem",
				}}
			>
				<div className="flex justify-between items-center mb-8">
					<div>
						<h2 className="text-2xl font-black tracking-tight">
							{editingReceipt ? "Edit Receipt" : "New Receipt"}
						</h2>
						<p className="text-sm text-muted">
							{editingReceipt
								? "Update transaction details."
								: "Record details and allocate funds."}
						</p>
					</div>
					<button className="btn btn-ghost p-2 rounded-full" onClick={onClose}>
						<X size={20} />
					</button>
				</div>

				<div className="space-y-6">
					{/* Upload Progress Widget */}
					{(isUploading || uploadError || (uploadedFileHash && uploadedFileName)) && (
						<div className="mb-6">
							<UploadProgressWidget
								isUploading={isUploading}
								uploadProgress={uploadProgress}
								fileName={uploadedFileName || uploadingFile?.file.name}
								error={uploadError}
							/>
						</div>
					)}

					{/* Download File Section (when editing with an existing file) */}
					{editingReceipt?.hash && (
						<div className="mb-6">
							<label className="label-caps">Attached File</label>
							<div className="flex items-center gap-3 p-3 rounded-lg bg-white/5 border border-white/10">
								<div className="flex-1">
									<p className="text-sm font-semibold">{editingReceipt.file || "Receipt file"}</p>
									<p className="text-xs text-muted">Hash: {editingReceipt.hash.substring(0, 12)}...</p>
								</div>
								<button
									className="btn btn-ghost flex items-center gap-2 px-4 py-2"
									onClick={handleDownload}
									disabled={isDownloading}
								>
									<Download size={16} />
									{isDownloading ? "Downloading..." : "Download"}
								</button>
							</div>
							{downloadError && (
								<p className="text-xs text-error mt-2">{downloadError}</p>
							)}
						</div>
					)}

					{/* Top Fields Structure */}
					<div className="grid grid-cols-2 gap-6">
						{/* Left Column: Vendor & Reference */}
						<div className="space-y-6">
							<div>
								<label className="label-caps">Vendor</label>
								<input
									ref={vendorRef}
									className="w-full text-lg font-semibold"
									placeholder="e.g. Amazon"
									value={vendor}
									onChange={(e) => setVendor(e.target.value)}
								/>
							</div>
							<div>
								<label className="label-caps">Reference (optional)</label>
								<div style={{ position: "relative" }}>
									<Tag
										size={16}
										className="text-muted"
										style={{
											position: "absolute",
											left: "12px",
											top: "50%",
											transform: "translateY(-50%)",
										}}
									/>
									<input
										className="w-full text-sm"
										style={{ paddingLeft: "2.5rem" }}
										placeholder="Order / Invoice #"
										value={ref}
										onChange={(e) => setRef(e.target.value)}
									/>
								</div>
							</div>
						</div>

						{/* Right Column: Amount & DateTime */}
						<div className="space-y-6">
							<div>
								<label className="label-caps">Total Amount</label>
								<div style={{ position: "relative" }}>
									<DollarSign
										size={20}
										className="text-primary"
										style={{
											position: "absolute",
											left: "12px",
											top: "50%",
											transform: "translateY(-50%)",
										}}
									/>
									<input
										type="number"
										step="0.01"
										className="w-full text-lg font-bold"
										style={{ paddingLeft: "2.5rem" }}
										placeholder="0.00"
										value={total || ""}
										onChange={(e) =>
											handleTotalChange(parseFloat(e.target.value) || 0)
										}
									/>
								</div>
							</div>
							<div>
								<label className="label-caps">Date & Time</label>
								<div style={{ position: "relative" }}>
									<CalendarIcon
										size={16}
										className="text-muted"
										style={{
											position: "absolute",
											left: "12px",
											top: "50%",
											transform: "translateY(-50%)",
										}}
									/>
									<input
										type="datetime-local"
										className="w-full text-sm cursor-pointer"
										style={{ paddingLeft: "2.5rem" }}
										value={date}
										onChange={(e) => setDate(e.target.value)}
										onClick={(e) => (e.target as any).showPicker?.()}
									/>
								</div>
							</div>
						</div>
					</div>

					<hr
						style={{
							border: "none",
							borderTop: "1px solid rgba(255,255,255,0.05)",
							margin: "1rem 0",
						}}
					/>

					{/* Allocations Section */}
					<div>
						<div className="flex justify-between items-end mb-2">
							<label className="label-caps mb-0">Allocations</label>
							{isOverAllocated ? (
								<span className="text-[10px] font-black text-error uppercase tracking-wider">
									Over-allocated by ${(allocatedTotal - total).toFixed(2)}
								</span>
							) : (
								unallocatedAmount > 0 && (
									<span className="text-[10px] font-black text-warning uppercase tracking-wider">
										${unallocatedAmount.toFixed(2)} Remaining
									</span>
								)
							)}
						</div>

						{/* Breakdown Bar */}
						<div className="allocation-bar">
							{allocations.map((a, i) => {
								const percent = total > 0 ? (a.amount / total) * 100 : 0;
								return (
									<div
										key={a.bucketId}
										className="allocation-segment"
										style={{
											width: `${percent}%`,
											backgroundColor:
												SEGMENT_COLORS[i % SEGMENT_COLORS.length],
										}}
									/>
								);
							})}
							{unallocatedAmount > 0 && (
								<div
									className="allocation-segment"
									style={{
										width: `${(unallocatedAmount / total) * 100}%`,
										backgroundColor: "rgba(255,255,255,0.05)",
									}}
								/>
							)}
						</div>

						<div className="min-h-[60px]">
							<AnimatePresence initial={false}>
								{allocations.map((allocation, index) => {
									const bucket = buckets.find(
										(b) => b.id === allocation.bucketId,
									);
									const isManual = manualAllocations.has(allocation.bucketId);
									const percent =
										total > 0 ? (allocation.amount / total) * 100 : 0;

									return (
										<motion.div
											key={allocation.bucketId}
											initial={{ opacity: 0, y: -10 }}
											animate={{ opacity: 1, y: 0 }}
											exit={{ opacity: 0, scale: 0.95 }}
											className={`allocation-row ${isManual ? "manual" : ""}`}
										>
											<div className="flex items-center gap-3 flex-1 min-w-0">
												<div
													className="w-2.5 h-2.5 rounded-full flex-shrink-0"
													style={{
														backgroundColor:
															SEGMENT_COLORS[index % SEGMENT_COLORS.length],
													}}
												/>
												<span className="text-sm font-semibold truncate">
													{bucket?.name}
												</span>
											</div>

											<div className="flex items-center gap-4">
												<button
													onClick={() => toggleManual(allocation.bucketId)}
													className={`icon-btn ${isManual ? "active" : ""}`}
													title={
														isManual
															? "Manual entry - Click to auto-split"
															: "Auto-splitting - Click to lock amount"
													}
												>
													{isManual ? <Lock size={16} /> : <Unlock size={16} />}
												</button>

												<div className="flex items-center gap-2">
													<label className="text-muted text-[10px]">$</label>
													<input
														type="number"
														step="0.01"
														className="allocation-input"
														value={allocation.amount || ""}
														onChange={(e) =>
															handleManualAmount(
																allocation.bucketId,
																parseFloat(e.target.value) || 0,
															)
														}
													/>
												</div>

												<span className="text-[10px] text-muted w-8 text-right font-mono font-bold">
													{percent.toFixed(0)}%
												</span>

												<button
													onClick={() =>
														handleRemoveBucket(allocation.bucketId)
													}
													className="icon-btn danger"
													title="Remove allocation"
												>
													<Trash2 size={16} />
												</button>
											</div>
										</motion.div>
									);
								})}
							</AnimatePresence>

							{allocations.length === 0 && (
								<div className="text-center py-6 text-muted text-[10px] font-bold uppercase tracking-widest border-2 border-dashed border-white/5 rounded-xl">
									Choose a category below
								</div>
							)}
						</div>

						{/* Quick Add Chips */}
						<div className="mt-4 flex flex-wrap gap-1">
							{availableBuckets.map((bucket) => (
								<button
									key={bucket.id}
									className="chip"
									onClick={() => handleAddBucket(bucket.id)}
								>
									<Plus size={12} />
									{bucket.name}
								</button>
							))}
						</div>
					</div>

					<div>
						<label className="label-caps">Notes</label>
						<textarea
							className="w-full h-20 resize-none text-sm"
							placeholder="Any additional details..."
							value={notes}
							onChange={(e) => setNotes(e.target.value)}
						/>
					</div>
				</div>

				<div className="mt-10 flex gap-4">
					{editingReceipt && (
						<button
							className="btn btn-ghost flex-1 py-3 text-error hover:bg-error/10"
							onClick={handleDelete}
						>
							Delete Receipt
						</button>
					)}
					<button
						className={`btn btn-primary justify-center py-3 text-base ${editingReceipt ? 'flex-1' : 'w-full'
							}`}
						onClick={handleSave}
						disabled={!vendor || total <= 0 || isOverAllocated}
					>
						Save Receipt
					</button>
				</div>
			</motion.div>
		</div>
	);
};

export default ReceiptModal;
