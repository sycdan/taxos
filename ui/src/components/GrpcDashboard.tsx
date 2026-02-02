import React, { useState, useEffect } from "react";
import apiClient from "../api/client";
import type { Bucket } from "../api/client";

interface DashboardData {
	buckets: Array<{
		bucket: Bucket;
		totalAmount: number;
		receiptCount: number;
	}>;
	totalAmount: number;
	totalReceipts: number;
}

const GrpcDashboard: React.FC = () => {
	const [dashboardData, setDashboardData] = useState<DashboardData | null>(
		null,
	);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [dateRange, setDateRange] = useState({
		startDate: new Date(new Date().getFullYear(), 0, 1), // Start of current year
		endDate: new Date(),
	});

	const loadDashboard = async () => {
		try {
			setLoading(true);
			setError(null);

			const response = await apiClient.getDashboard({
				startDate: dateRange.startDate,
				endDate: dateRange.endDate,
				includeEmptyBuckets: true,
			});

			setDashboardData({
				buckets: response.bucketSummaries.map((summary) => ({
					bucket: summary.bucket!,
					totalAmount: summary.totalAmount,
					receiptCount: summary.receiptCount,
				})),
				totalAmount: response.totalAmount,
				totalReceipts: response.totalReceipts,
			});
		} catch (err) {
			setError(err instanceof Error ? err.message : "Failed to load dashboard");
		} finally {
			setLoading(false);
		}
	};

	const createBucket = async (name: string, description: string) => {
		try {
			await apiClient.createBucket(name, description);
			await loadDashboard(); // Refresh the dashboard
		} catch (err) {
			setError(err instanceof Error ? err.message : "Failed to create bucket");
		}
	};

	useEffect(() => {
		loadDashboard();
	}, [dateRange]);

	if (loading) {
		return (
			<div className="flex items-center justify-center min-h-screen">
				<div className="text-lg">Loading dashboard...</div>
			</div>
		);
	}

	if (error) {
		return (
			<div className="flex items-center justify-center min-h-screen">
				<div className="text-red-500 text-lg">Error: {error}</div>
			</div>
		);
	}

	return (
		<div className="p-6 max-w-6xl mx-auto">
			<h1 className="text-3xl font-bold mb-6">TaxOS Dashboard</h1>

			{/* Date Range Selector */}
			<div className="mb-6 flex gap-4 items-center">
				<label className="flex flex-col">
					<span className="text-sm font-medium mb-1">Start Date</span>
					<input
						type="date"
						value={dateRange.startDate.toISOString().split("T")[0]}
						onChange={(e) =>
							setDateRange((prev) => ({
								...prev,
								startDate: new Date(e.target.value),
							}))
						}
						className="border rounded px-3 py-2"
					/>
				</label>

				<label className="flex flex-col">
					<span className="text-sm font-medium mb-1">End Date</span>
					<input
						type="date"
						value={dateRange.endDate.toISOString().split("T")[0]}
						onChange={(e) =>
							setDateRange((prev) => ({
								...prev,
								endDate: new Date(e.target.value),
							}))
						}
						className="border rounded px-3 py-2"
					/>
				</label>
			</div>

			{/* Summary Cards */}
			<div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
				<div className="bg-blue-50 p-4 rounded-lg">
					<h3 className="text-lg font-semibold text-blue-800">Total Amount</h3>
					<p className="text-2xl font-bold text-blue-900">
						${dashboardData?.totalAmount.toFixed(2) || "0.00"}
					</p>
				</div>

				<div className="bg-green-50 p-4 rounded-lg">
					<h3 className="text-lg font-semibold text-green-800">
						Total Receipts
					</h3>
					<p className="text-2xl font-bold text-green-900">
						{dashboardData?.totalReceipts || 0}
					</p>
				</div>

				<div className="bg-purple-50 p-4 rounded-lg">
					<h3 className="text-lg font-semibold text-purple-800">
						Active Buckets
					</h3>
					<p className="text-2xl font-bold text-purple-900">
						{dashboardData?.buckets.filter((b) => b.receiptCount > 0).length ||
							0}
					</p>
				</div>
			</div>

			{/* Buckets List */}
			<div className="bg-white shadow rounded-lg">
				<div className="p-4 border-b">
					<h2 className="text-xl font-semibold">Expense Buckets</h2>
				</div>

				<div className="p-4">
					{dashboardData?.buckets.length === 0 ? (
						<p className="text-gray-500 text-center py-8">
							No buckets found. Create your first bucket to get started.
						</p>
					) : (
						<div className="grid gap-4">
							{dashboardData?.buckets.map((bucketSummary) => (
								<BucketCard
									key={bucketSummary.bucket.id}
									bucketSummary={bucketSummary}
								/>
							))}
						</div>
					)}
				</div>
			</div>

			{/* Create Bucket Form */}
			<CreateBucketForm onCreateBucket={createBucket} />
		</div>
	);
};

interface BucketCardProps {
	bucketSummary: {
		bucket: Bucket;
		totalAmount: number;
		receiptCount: number;
	};
}

const BucketCard: React.FC<BucketCardProps> = ({ bucketSummary }) => {
	const { bucket, totalAmount, receiptCount } = bucketSummary;

	return (
		<div className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
			<div className="flex justify-between items-start">
				<div>
					<h3 className="font-semibold text-lg">{bucket.name}</h3>
					{bucket.description && (
						<p className="text-gray-600 mt-1">{bucket.description}</p>
					)}
				</div>

				<div className="text-right">
					<p className="text-xl font-bold">${totalAmount.toFixed(2)}</p>
					<p className="text-sm text-gray-500">
						{receiptCount} receipt{receiptCount !== 1 ? "s" : ""}
					</p>
				</div>
			</div>
		</div>
	);
};

interface CreateBucketFormProps {
	onCreateBucket: (name: string, description: string) => Promise<void>;
}

const CreateBucketForm: React.FC<CreateBucketFormProps> = ({
	onCreateBucket,
}) => {
	const [isOpen, setIsOpen] = useState(false);
	const [name, setName] = useState("");
	const [description, setDescription] = useState("");
	const [isSubmitting, setIsSubmitting] = useState(false);

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		if (!name.trim()) return;

		setIsSubmitting(true);
		try {
			await onCreateBucket(name.trim(), description.trim());
			setName("");
			setDescription("");
			setIsOpen(false);
		} catch (err) {
			// Error handling is done in parent component
		} finally {
			setIsSubmitting(false);
		}
	};

	if (!isOpen) {
		return (
			<div className="mt-6">
				<button
					onClick={() => setIsOpen(true)}
					className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors"
				>
					Create New Bucket
				</button>
			</div>
		);
	}

	return (
		<div className="mt-6 bg-white shadow rounded-lg p-4">
			<h3 className="text-lg font-semibold mb-4">Create New Bucket</h3>

			<form onSubmit={handleSubmit} className="space-y-4">
				<div>
					<label className="block text-sm font-medium mb-1">
						Bucket Name *
					</label>
					<input
						type="text"
						value={name}
						onChange={(e) => setName(e.target.value)}
						className="w-full border rounded px-3 py-2"
						placeholder="e.g., Office Supplies, Travel Expenses"
						required
					/>
				</div>

				<div>
					<label className="block text-sm font-medium mb-1">Description</label>
					<textarea
						value={description}
						onChange={(e) => setDescription(e.target.value)}
						className="w-full border rounded px-3 py-2"
						rows={3}
						placeholder="Optional description of this expense category"
					/>
				</div>

				<div className="flex gap-2">
					<button
						type="submit"
						disabled={!name.trim() || isSubmitting}
						className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
					>
						{isSubmitting ? "Creating..." : "Create Bucket"}
					</button>

					<button
						type="button"
						onClick={() => setIsOpen(false)}
						className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition-colors"
					>
						Cancel
					</button>
				</div>
			</form>
		</div>
	);
};

export default GrpcDashboard;
