import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Edit2, Check, X, Tag } from "lucide-react";
import type { Vendor } from "../types";

interface VendorManagerProps {
	vendors: Vendor[];
	onUpdateVendor: (id: string, name: string) => Promise<Vendor | null>;
	onRefresh: () => Promise<void>;
}

const VendorManager: React.FC<VendorManagerProps> = ({
	vendors,
	onUpdateVendor,
	onRefresh,
}) => {
	const [editingId, setEditingId] = useState<string | null>(null);
	const [editName, setEditName] = useState("");
	const [saving, setSaving] = useState(false);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		onRefresh();
	}, [onRefresh]);

	const startEditing = (vendor: Vendor) => {
		setEditingId(vendor.id);
		setEditName(vendor.name);
		setError(null);
	};

	const cancelEdit = () => {
		setEditingId(null);
		setEditName("");
		setError(null);
	};

	const saveEdit = async () => {
		if (!editingId || !editName.trim()) return;
		setSaving(true);
		setError(null);
		const result = await onUpdateVendor(editingId, editName.trim());
		setSaving(false);
		if (result) {
			setEditingId(null);
		} else {
			setError("Failed to save. Please try again.");
		}
	};

	return (
		<motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
			<div className="flex justify-between items-center mb-8">
				<div>
					<h1 className="text-3xl mb-2">Vendors</h1>
					<p className="text-muted">
						Manage your vendors. Click the edit icon to rename a vendor.
					</p>
				</div>
			</div>

			{vendors.length === 0 ? (
				<div className="card text-center py-16 text-muted">
					<Tag size={40} className="mx-auto mb-4 opacity-40" />
					<p className="text-lg">No vendors yet.</p>
					<p className="text-sm mt-1">
						Vendors are created automatically when you add receipts.
					</p>
				</div>
			) : (
				<div
					style={{
						display: "grid",
						gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
						gap: "1.5rem",
					}}
				>
					{vendors.map((vendor, index) => (
						<motion.div
							key={vendor.id}
							initial={{ opacity: 0, scale: 0.95 }}
							animate={{ opacity: 1, scale: 1 }}
							transition={{ delay: index * 0.05 }}
							className="card group"
						>
							<div className="flex justify-between items-start mb-4">
								<div className="p-2 bg-primary/10 rounded-lg text-primary">
									<Tag size={20} />
								</div>

								<div className="flex gap-2">
									{editingId === vendor.id ? (
										<>
											<button
												className="btn btn-ghost p-1 text-primary"
												onClick={saveEdit}
												disabled={saving || !editName.trim()}
												title="Save"
											>
												<Check size={18} />
											</button>
											<button
												className="btn btn-ghost p-1 text-muted"
												onClick={cancelEdit}
												disabled={saving}
												title="Cancel"
											>
												<X size={18} />
											</button>
										</>
									) : (
										<button
											className="btn btn-ghost p-1 text-muted group-hover:text-primary transition-colors"
											onClick={() => startEditing(vendor)}
											title="Rename vendor"
										>
											<Edit2 size={18} />
										</button>
									)}
								</div>
							</div>

							{editingId === vendor.id ? (
								<div className="flex flex-col gap-1">
									<input
										autoFocus
										className="w-full text-lg font-bold mb-1"
										value={editName}
										onChange={(e) => setEditName(e.target.value)}
										onKeyDown={(e) => {
											if (e.key === "Enter") saveEdit();
											if (e.key === "Escape") cancelEdit();
										}}
										disabled={saving}
									/>
									{error && (
										<div className="text-error text-[10px] font-semibold">
											{error}
										</div>
									)}
								</div>
							) : (
								<div
									className="text-xl font-bold mb-1 cursor-pointer hover:text-primary transition-colors"
									onClick={() => startEditing(vendor)}
									title="Click to rename"
								>
									{vendor.name}
								</div>
							)}
						</motion.div>
					))}
				</div>
			)}
		</motion.div>
	);
};

export default VendorManager;
