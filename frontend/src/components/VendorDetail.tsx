import React, { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Edit2, Check, X } from "lucide-react";
import type { Receipt } from "../types";
import { format } from "date-fns";
import { useTaxos } from "../contexts/TaxosContext";

interface VendorDetailProps {
	vendorId: string;
	onBack: () => void;
	onEditReceipt: (receipt: Receipt) => void;
}

const VendorDetail: React.FC<VendorDetailProps> = ({
	vendorId,
	onBack,
	onEditReceipt,
}) => {
	const { vendors, receipts, updateVendor } = useTaxos();

	const [isEditing, setIsEditing] = useState(false);
	const [editName, setEditName] = useState("");

	const isGuid = (value: string) => /^[0-9a-f]{32}$/i.test(value);
	const resolvedVendor =
		vendors.find((v) => v.id === vendorId) ??
		vendors.find((v) => v.name === vendorId);
	const resolvedVendorId = resolvedVendor?.id ?? vendorId;
	const vendorName = resolvedVendor?.name ?? vendorId;

	const handleStartEdit = () => {
		setEditName(vendorName);
		setIsEditing(true);
	};

	const handleSaveEdit = async () => {
		if (!editName.trim() || editName.trim() === vendorName) {
			setIsEditing(false);
			return;
		}
		if (!isGuid(resolvedVendorId)) {
			console.error("Cannot rename vendor: unresolved vendor GUID", {
				vendorId,
				resolvedVendorId,
			});
			return;
		}
		const result = await updateVendor(resolvedVendorId, editName.trim());
		if (result) setIsEditing(false);
	};

	// Derive receipts for this vendor directly from the in-memory receipts map —
	// no API call needed. Receipts store vendor name, so filter by name.
	const sortedReceipts = useMemo(() => {
		return Object.values(receipts)
			.filter((r) => r.vendor === vendorName)
			.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
	}, [receipts, vendorName]);

	const totalAmount = useMemo(() => {
		return sortedReceipts.reduce((sum, r) => sum + r.total, 0);
	}, [sortedReceipts]);

	const totalAllocated = useMemo(() => {
		return sortedReceipts.reduce((sum, r) => {
			return sum + r.allocations.reduce((s, a) => s + a.amount, 0);
		}, 0);
	}, [sortedReceipts]);

	const remainingToAllocate = totalAmount - totalAllocated;

	return (
		<motion.div
			initial={{ opacity: 0, y: 20 }}
			animate={{ opacity: 1, y: 0 }}
			className="space-y-6"
		>
			<div className="flex items-center gap-4 mb-6">
				<button className="btn btn-ghost p-1" onClick={onBack}>
					<ArrowLeft size={20} />
				</button>
				<div className="flex-1">
					{isEditing ? (
						<div className="flex items-center gap-2">
							<input
								autoFocus
								className="text-2xl font-bold bg-transparent border-b-2 border-primary focus:outline-none"
								value={editName}
								onChange={(e) => setEditName(e.target.value)}
								onKeyDown={(e) => {
									if (e.key === "Enter") void handleSaveEdit();
									if (e.key === "Escape") setIsEditing(false);
								}}
							/>
							<button
								className="icon-btn active"
								onClick={() => void handleSaveEdit()}
								disabled={!editName.trim()}
							>
								<Check size={20} />
							</button>
							<button className="icon-btn" onClick={() => setIsEditing(false)}>
								<X size={20} />
							</button>
						</div>
					) : (
						<div className="flex items-center gap-4 group/header">
							<h2 className="text-2xl font-bold">{vendorName}</h2>
							<button
								className="icon-btn opacity-0 group-hover/header:opacity-100 transition-opacity"
								onClick={handleStartEdit}
								title="Rename Vendor"
							>
								<Edit2 size={18} />
							</button>
						</div>
					)}
					<p className="text-muted text-sm">
						{sortedReceipts.length} receipt
						{sortedReceipts.length !== 1 ? "s" : ""}
					</p>
				</div>
			</div>

			<div className="grid grid-cols-3 gap-4">
				<div className="card">
					<div className="text-muted text-sm uppercase font-semibold mb-2">
						Total
					</div>
					<div className="text-2xl font-bold">
						$
						{totalAmount.toLocaleString(undefined, {
							minimumFractionDigits: 2,
						})}
					</div>
				</div>
				<div className="card">
					<div className="text-muted text-sm uppercase font-semibold mb-2">
						Allocated
					</div>
					<div className="text-2xl font-bold text-primary">
						$
						{totalAllocated.toLocaleString(undefined, {
							minimumFractionDigits: 2,
						})}
					</div>
				</div>
				<div className="card">
					<div className="text-muted text-sm uppercase font-semibold mb-2">
						Remaining
					</div>
					<div
						className={`text-2xl font-bold ${remainingToAllocate > 0 ? "text-warning" : "text-success"}`}
					>
						$
						{remainingToAllocate.toLocaleString(undefined, {
							minimumFractionDigits: 2,
						})}
					</div>
				</div>
			</div>

			<div className="space-y-2">
				<h3 className="text-lg font-semibold">Receipts</h3>
				<div className="space-y-2">
					{sortedReceipts.length === 0 ? (
						<div className="card text-center py-8 text-muted">
							No receipts for this vendor in the selected date range.
						</div>
					) : (
						sortedReceipts.map((receipt) => {
							const allocatedAmount = receipt.allocations.reduce(
								(sum, a) => sum + a.amount,
								0,
							);
							const remainingAmount = receipt.total - allocatedAmount;

							return (
								<motion.div
									key={receipt.id}
									initial={{ opacity: 0, x: -20 }}
									animate={{ opacity: 1, x: 0 }}
									className="card cursor-pointer hover:bg-slate-900/50 transition-colors p-4 group"
									onClick={() => onEditReceipt(receipt)}
								>
									<div className="flex items-start justify-between mb-2">
										<div className="flex-1">
											<div className="text-sm uppercase font-semibold text-muted">
												{format(new Date(receipt.date), "MMM d, yyyy")}
											</div>
											{receipt.notes && (
												<div className="text-sm text-muted mt-1">
													{receipt.notes}
												</div>
											)}
										</div>
										<Edit2
											className="text-muted group-hover:text-primary transition-colors"
											size={16}
										/>
									</div>
									<div className="flex items-baseline justify-between">
										<div className="text-lg font-bold">
											$
											{receipt.total.toLocaleString(undefined, {
												minimumFractionDigits: 2,
											})}
										</div>
										<div className="flex gap-2 text-xs font-semibold">
											<span className="text-primary">
												$
												{allocatedAmount.toLocaleString(undefined, {
													minimumFractionDigits: 2,
												})}
											</span>
											{remainingAmount > 0 && (
												<span className="text-warning">
													$
													{remainingAmount.toLocaleString(undefined, {
														minimumFractionDigits: 2,
													})}
												</span>
											)}
										</div>
									</div>
								</motion.div>
							);
						})
					)}
				</div>
			</div>
		</motion.div>
	);
};

export default VendorDetail;
