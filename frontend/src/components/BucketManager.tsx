import React, { useState } from "react";
import { motion } from "framer-motion";
import { Plus, Edit2, Check, X, Database, Trash2 } from "lucide-react";
import type { Bucket } from "../types";

interface BucketManagerProps {
	buckets: Bucket[];
	onAddBucket: (name: string) => void;
	onUpdateBucket: (id: string, name: string) => void;
	onDeleteBucket: (id: string) => void;
	isNameTaken: (name: string, excludeId?: string) => boolean;
}

const BucketManager: React.FC<BucketManagerProps> = ({
	buckets,
	onAddBucket,
	onUpdateBucket,
	onDeleteBucket,
	isNameTaken,
}) => {
	const [newBucketName, setNewBucketName] = useState("");
	const [editingId, setEditingId] = useState<string | null>(null);
	const [editName, setEditName] = useState("");

	const handleAdd = (e: React.FormEvent) => {
		e.preventDefault();
		if (newBucketName.trim()) {
			onAddBucket(newBucketName.trim());
			setNewBucketName("");
		}
	};

	const startEditing = (bucket: Bucket) => {
		setEditingId(bucket.id);
		setEditName(bucket.name);
	};

	const saveEdit = () => {
		if (editingId && editName.trim()) {
			// If name is not taken (excluding itself)
			if (!isNameTaken(editName.trim(), editingId)) {
				onUpdateBucket(editingId, editName.trim());
				setEditingId(null);
			}
		}
	};

	return (
		<motion.div
			initial={{ opacity: 0, y: 10 }}
			animate={{ opacity: 1, y: 0 }}
			className="bucket-manager"
		>
			<div className="flex justify-between items-center mb-8">
				<div>
					<h1 className="text-3xl mb-2">Bucket Management</h1>
					<p className="text-muted">
						Create and organize your spending categories.
					</p>
				</div>
			</div>

			<form onSubmit={handleAdd} className="mb-12 flex flex-col gap-2">
				<div className="flex gap-4">
					<input
						type="text"
						placeholder="New bucket name (e.g. Travel, Office Supplies)"
						className={`flex-1 ${newBucketName.trim() && isNameTaken(newBucketName) ? "border-error" : ""}`}
						value={newBucketName}
						onChange={(e) => setNewBucketName(e.target.value)}
					/>
					<button
						type="submit"
						className="btn btn-primary"
						disabled={!newBucketName.trim() || isNameTaken(newBucketName)}
					>
						<Plus size={20} />
						<span>Add Bucket</span>
					</button>
				</div>
				{newBucketName.trim() && isNameTaken(newBucketName) && (
					<div className="text-error text-xs font-semibold ml-2">
						This bucket name is already taken.
					</div>
				)}
			</form>

			<div
				className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
				style={{
					display: "grid",
					gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
					gap: "1.5rem",
				}}
			>
				{buckets.map((bucket, index) => (
					<motion.div
						key={bucket.id}
						initial={{ opacity: 0, scale: 0.95 }}
						animate={{ opacity: 1, scale: 1 }}
						transition={{ delay: index * 0.05 }}
						className="card group"
					>
						<div className="flex justify-between items-start mb-4">
							<div className="p-2 bg-primary/10 rounded-lg text-primary">
								<Database size={20} />
							</div>

							<div className="flex gap-2">
								{editingId === bucket.id ? (
									<>
										<button
											className="btn btn-ghost p-1 text-primary"
											onClick={saveEdit}
											disabled={
												!editName.trim() || isNameTaken(editName, bucket.id)
											}
										>
											<Check size={18} />
										</button>
										<button
											className="btn btn-ghost p-1 text-muted"
											onClick={() => setEditingId(null)}
										>
											<X size={18} />
										</button>
									</>
								) : (
									<>
										<button
											className="btn btn-ghost p-1 text-muted group-hover:text-primary transition-colors"
											onClick={() => startEditing(bucket)}
										>
											<Edit2 size={18} />
										</button>
										<button
											className="btn btn-ghost p-1 text-muted hover:text-error transition-colors"
											onClick={() => onDeleteBucket(bucket.id)}
											title="Delete Bucket"
										>
											<Trash2 size={18} />
										</button>
									</>
								)}
							</div>
						</div>

						{editingId === bucket.id ? (
							<div className="flex flex-col gap-1">
								<input
									autoFocus
									className={`w-full text-lg font-bold mb-1 ${editName.trim() && isNameTaken(editName, bucket.id) ? "border-error" : ""}`}
									value={editName}
									onChange={(e) => setEditName(e.target.value)}
									onKeyDown={(e) => e.key === "Enter" && saveEdit()}
								/>
								{editName.trim() && isNameTaken(editName, bucket.id) && (
									<div className="text-error text-[10px] font-semibold">
										Name already taken
									</div>
								)}
							</div>
						) : (
							<div
								className="text-xl font-bold mb-1 cursor-pointer hover:text-primary transition-colors"
								onClick={() => startEditing(bucket)}
								title="Click to rename"
							>
								{bucket.name}
							</div>
						)}
					</motion.div>
				))}
			</div>
		</motion.div>
	);
};

export default BucketManager;
