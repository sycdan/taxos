import React, { useMemo, useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Edit2 } from "lucide-react";
import type { Receipt } from "../types";
import { format } from "date-fns";
import { useTaxos } from "../contexts/TaxosContext";

interface VendorDetailProps {
	vendor: string;
	onBack: () => void;
	startDate: Date;
	endDate: Date;
	onEditReceipt: (receipt: Receipt) => void;
}

const VendorDetail: React.FC<VendorDetailProps> = ({
	vendor,
	onBack,
	startDate,
	endDate,
	onEditReceipt,
}) => {
	const { loadReceiptsForVendor, currentReceiptsList, setActiveBucketId } =
		useTaxos();

	// Fetch receipts when vendor changes or date range changes
	useEffect(() => {
		setActiveBucketId(null);
		const fetchReceipts = async () => {
			try {
				await loadReceiptsForVendor(vendor, startDate, endDate);
			} catch (error) {
				console.error("Failed to fetch receipts:", error);
			}
		};
		void fetchReceipts();
	}, [vendor, startDate, endDate, setActiveBucketId, loadReceiptsForVendor]);

	const sortedReceipts = useMemo(() => {
		return [...currentReceiptsList].sort((a, b) => {
			return new Date(b.date).getTime() - new Date(a.date).getTime();
		});
	}, [currentReceiptsList]);

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
				<div>
					<h2 className="text-2xl font-bold">{vendor}</h2>
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
