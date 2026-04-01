import React, { useMemo } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Receipt as ReceiptIcon, Calendar, Hash } from "lucide-react";
import type { Receipt } from "../types";
import { format } from "date-fns";
import { useTaxos } from "../contexts/TaxosContext";

interface UnallocatedDetailProps {
	onBack: () => void;
	onEditReceipt: (receipt: Receipt) => void;
}

const UnallocatedDetail: React.FC<UnallocatedDetailProps> = ({
	onBack,
	onEditReceipt,
}) => {
	const { unallocatedReceipts, unallocatedSummary } = useTaxos();

	const sortedReceipts = useMemo(() => {
		return [...unallocatedReceipts].sort(
			(a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
		);
	}, [unallocatedReceipts]);

	return (
		<motion.div
			initial={{ opacity: 0, x: 20 }}
			animate={{ opacity: 1, x: 0 }}
			className="bucket-detail"
		>
			<button className="btn btn-ghost mb-6 group" onClick={onBack}>
				<ArrowLeft
					size={20}
					className="group-hover:-translate-x-1 transition-transform"
				/>
				Back to Dashboard
			</button>

			<div className="flex justify-between items-end mb-8">
				<div className="flex-1">
					<h1 className="text-3xl font-bold">Unallocated</h1>
					<p className="text-muted mt-2">
						Receipts with amounts not yet assigned to a bucket.
					</p>
				</div>
				<div className="text-right">
					<div className="text-xs text-muted uppercase font-bold">
						Unallocated Total
					</div>
					<div className="text-4xl font-bold text-primary">
						$
						{unallocatedSummary.totalAmount.toLocaleString(undefined, {
							minimumFractionDigits: 2,
							maximumFractionDigits: 2,
						})}
					</div>
				</div>
			</div>

			<div
				className="space-y-4"
				style={{ display: "flex", flexDirection: "column", gap: "1rem" }}
			>
				{sortedReceipts.length === 0 ? (
					<div className="card text-center py-20 border-dashed">
						<ReceiptIcon
							size={48}
							className="mx-auto text-muted mb-4 opacity-20"
						/>
						<p className="text-muted">No unallocated receipts for this period.</p>
					</div>
				) : (
					sortedReceipts.map((receipt) => {
						const allocatedAmount = receipt.allocations.reduce(
							(sum, a) => sum + a.amount,
							0,
						);
						const unallocatedAmount = receipt.total - allocatedAmount;

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
											<span className="flex items-center gap-1">
												<Calendar size={12} />{" "}
												{format(new Date(receipt.date), "MMM d, h:mm a")}
											</span>
											{receipt.ref && (
												<span className="flex items-center gap-1">
													<Hash size={12} /> {receipt.ref}
												</span>
											)}
										</div>
									</div>
								</div>

								<div className="text-right">
									<div className="text-xl font-bold">
										$
										{unallocatedAmount.toLocaleString(undefined, {
											minimumFractionDigits: 2,
											maximumFractionDigits: 2,
										})}
									</div>
									<div className="text-xs text-muted">
										Total: ${receipt.total.toFixed(2)}
									</div>
								</div>
							</motion.div>
						);
					})
				)}
			</div>
		</motion.div>
	);
};

export default UnallocatedDetail;
