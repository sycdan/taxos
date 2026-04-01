import React, { useState, useEffect, useMemo } from "react";
import {
	Plus,
	LayoutDashboard,
	ArrowLeft,
	LogOut,
	Upload,
	Tag,
} from "lucide-react";
import Dashboard from "./components/Dashboard";
import BucketDetail from "./components/BucketDetail";
import VendorDetail from "./components/VendorDetail";
import UnallocatedDetail from "./components/UnallocatedDetail";
import ReceiptModal from "./components/ReceiptModal";
import LoginModal from "./components/LoginModal";
import { useTaxos } from "./contexts/TaxosContext";
import { clearToken } from "./api/client";
import {
	format,
	startOfMonth,
	endOfMonth,
	startOfYear,
	endOfYear,
} from "date-fns";
import type { Receipt } from "./types";
import { sha256 } from "js-sha256";

type FilterMode = "year" | "month";

interface FilterConfig {
	mode: FilterMode;
	value: string;
}

interface ToastState {
	message: string;
	kind: "error";
}

const App: React.FC = () => {
	const {
		buckets,
		bucketSummaries,
		vendorNames,
		addReceipt,
		updateReceipt,
		deleteReceipt,
		addBucket,
		updateBucket,
		deleteBucket,
		isNameTaken,
		authenticated,
	} = useTaxos();

	const [currentBucketId, setCurrentBucketId] = useState<string | null>(null);
	const [selectedVendor, setSelectedVendor] = useState<string | null>(null);
	const [showVendors, setShowVendors] = useState(false);
	const [showUnallocated, setShowUnallocated] = useState(false);
	const [isModalOpen, setIsModalOpen] = useState(false);
	const [uploadedFile, setUploadedFile] = useState<string | undefined>(
		undefined,
	);
	const [editingReceipt, setEditingReceipt] = useState<Receipt | undefined>(
		undefined,
	);
	const [showEmpty, setShowEmpty] = useState(false);
	const [showLoginModal, setShowLoginModal] = useState(!authenticated);
	const [uploadingFile, setUploadingFile] = useState<
		{ file: File; hash: string } | undefined
	>();
	const [toast, setToast] = useState<ToastState | null>(null);

	const [filterConfig, setFilterConfig] = useState<FilterConfig>(() => {
		try {
			const saved = localStorage.getItem("taxos_filter_config");
			if (saved) return JSON.parse(saved);
		} catch (error) {
			console.error("Failed to parse filter config", error);
		}
		return {
			mode: "month",
			value: format(new Date(), "yyyy-MM"),
		};
	});

	useEffect(() => {
		localStorage.setItem("taxos_filter_config", JSON.stringify(filterConfig));
	}, [filterConfig]);

	useEffect(() => {
		if (!toast) return;
		const timeout = window.setTimeout(() => setToast(null), 5000);
		return () => window.clearTimeout(timeout);
	}, [toast]);

	const totalAllocated = useMemo(() => {
		return bucketSummaries.reduce((sum, summary) => sum + summary.totalAmount, 0);
	}, [bucketSummaries]);

	const dateRange = useMemo(() => {
		try {
			if (filterConfig.mode === "year") {
				const year =
					parseInt(filterConfig.value, 10) || new Date().getFullYear();
				const date = new Date(year, 0, 1);
				return {
					start: startOfYear(date),
					end: endOfYear(date),
				};
			}

			const [year, month] = (
				filterConfig.value || format(new Date(), "yyyy-MM")
			)
				.split("-")
				.map(Number);
			const date =
				isNaN(year) || isNaN(month) ? new Date() : new Date(year, month - 1, 1);
			return {
				start: startOfMonth(date),
				end: endOfMonth(date),
			};
		} catch (e) {
			console.error("Date parsing failed, falling back to current month", e);
			return { start: startOfMonth(new Date()), end: endOfMonth(new Date()) };
		}
	}, [filterConfig]);

	const handleModeToggle = () => {
		setFilterConfig((prev: FilterConfig): FilterConfig => {
			const isSwitchingToMonth = prev.mode === "year";
			return {
				mode: isSwitchingToMonth ? "month" : "year",
				value: isSwitchingToMonth
					? format(new Date(), "yyyy-MM")
					: format(dateRange.start, "yyyy"),
			};
		});
	};

	const handleValueChange = (value: string) => {
		if (!value) {
			setFilterConfig({
				mode: "year",
				value: format(new Date(), "yyyy"),
			});
			return;
		}
		setFilterConfig((prev: FilterConfig): FilterConfig => ({ ...prev, value }));
	};

	const calculateFileHash = async (file: File): Promise<string> => {
		const arrayBuffer = await file.arrayBuffer();
		if (crypto && crypto.subtle) {
			const hashBuffer = await crypto.subtle.digest("SHA-256", arrayBuffer);
			const hashArray = Array.from(new Uint8Array(hashBuffer));
			return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
		}
		return sha256(arrayBuffer);
	};

	const handleFileUpload = async (file: File) => {
		try {
			const hash = await calculateFileHash(file);
			setUploadingFile({ file, hash });
			setIsModalOpen(true);
		} catch (error) {
			console.error("Failed to process file:", error);
		}
	};

	const handleCloseModal = () => {
		setIsModalOpen(false);
		setUploadedFile(undefined);
		setEditingReceipt(undefined);
		setUploadingFile(undefined);
	};

	const handleEditReceipt = (receipt: Receipt) => {
		setEditingReceipt(receipt);
		setIsModalOpen(true);
	};

	const getErrorMessage = (error: unknown) => {
		const err = error as {
			message?: string;
			graphQLErrors?: Array<{ message?: string }>;
			networkError?: {
				result?: { errors?: Array<{ message?: string }> };
			};
			cause?: {
				result?: { errors?: Array<{ message?: string }> };
			};
		};

		const gqlMessage = err?.graphQLErrors
			?.map((e) => e?.message)
			.find(Boolean);
		if (gqlMessage) return gqlMessage;

		const networkGqlMessage = err?.networkError?.result?.errors
			?.map((e) => e?.message)
			.find(Boolean);
		if (networkGqlMessage) return networkGqlMessage;

		const causeGqlMessage = err?.cause?.result?.errors
			?.map((e) => e?.message)
			.find(Boolean);
		if (causeGqlMessage) return causeGqlMessage;

		if (error instanceof Error) return error.message;
		if (typeof error === "string") return error;
		return "Unable to save receipt. Please try again.";
	};

	const navigateToBuckets = () => {
		setCurrentBucketId(null);
		setSelectedVendor(null);
		setShowVendors(false);
		setShowUnallocated(false);
	};

	const navigateToVendors = () => {
		setCurrentBucketId(null);
		setSelectedVendor(null);
		setShowVendors(true);
	};

	if (!authenticated) {
		return (
			<LoginModal
				isOpen={showLoginModal && !authenticated}
				onLogin={() => setShowLoginModal(false)}
			/>
		);
	}

	return (
		<div className="app-layout">
			{toast && (
				<div className={`toast toast-${toast.kind}`} role="alert">
					<div className="toast-title">Could not save receipt</div>
					<div className="toast-message">{toast.message}</div>
				</div>
			)}

			<aside className="sidebar">
				<div className="logo mb-12">TAXOS</div>
				<nav className="flex flex-col gap-2 flex-1">
					<button
						className={`btn ${!showVendors ? "btn-primary" : "btn-ghost"} justify-start w-full`}
						onClick={navigateToBuckets}
					>
						<LayoutDashboard size={20} />
						<span>Buckets</span>
					</button>
					<button
						className={`btn ${showVendors ? "btn-primary" : "btn-ghost"} justify-start w-full`}
						onClick={navigateToVendors}
					>
						<Tag size={20} />
						<span>Vendors</span>
					</button>
					{authenticated && (
						<button
							className="btn btn-ghost justify-start w-full mt-auto text-red-600 hover:text-red-700"
							onClick={clearToken}
						>
							<LogOut size={20} />
							<span>Logout</span>
						</button>
					)}
				</nav>
			</aside>

			<div className="app-container">
				<header
					className="header"
					style={{ position: "sticky", top: "1rem", zIndex: 40 }}
				>
					<div className="flex items-center gap-4">
						{(currentBucketId || selectedVendor || showUnallocated) && (
							<button
								className="btn btn-ghost p-1"
								onClick={() => {
									setCurrentBucketId(null);
									setSelectedVendor(null);
									setShowUnallocated(false);
								}}
							>
								<ArrowLeft size={20} />
							</button>
						)}
						<div className="text-sm font-bold uppercase tracking-wider text-muted">
							Receipts
						</div>
						{!currentBucketId && !selectedVendor && !showVendors && !showUnallocated && (
							<>
								<div className="h-4 w-px bg-gray-600"></div>
								<div className="flex items-center gap-2">
									<span className="text-xs text-muted uppercase font-semibold">
										Total Allocated
									</span>
									<span className="text-sm font-bold text-primary">
										$
										{totalAllocated.toLocaleString(undefined, {
											minimumFractionDigits: 2,
											maximumFractionDigits: 2,
										})}
									</span>
								</div>
							</>
						)}
					</div>

					{!selectedVendor && (
						<div className="flex items-center gap-4">
							<div className="filter-group">
								<button
									className={`filter-mode-btn ${filterConfig.mode === "year" ? "active" : ""}`}
									onClick={handleModeToggle}
								>
									Year
								</button>
								<button
									className={`filter-mode-btn ${filterConfig.mode === "month" ? "active" : ""}`}
									onClick={handleModeToggle}
								>
									Month
								</button>
								<input
									className="filter-input"
									type={filterConfig.mode === "year" ? "number" : "month"}
									value={filterConfig.value}
									onChange={(e) => handleValueChange(e.target.value)}
									min="2000"
									max="2100"
									step="1"
								/>
							</div>
							<button
								className="btn btn-primary"
								onClick={() => setIsModalOpen(true)}
							>
								<Plus size={20} />
								<span>Add Receipt</span>
							</button>
							<input
								type="file"
								id="file-upload"
								className="hidden"
								style={{ display: "none" }}
								accept="image/*,application/pdf"
								onChange={(e) => {
									const files = e.target.files;
									if (files && files.length > 0) {
										handleFileUpload(files[0]);
									}
									e.target.value = "";
								}}
							/>
							<button
								className="btn btn-secondary"
								onClick={() => document.getElementById("file-upload")?.click()}
							>
								<Upload size={20} />
								<span>Upload File</span>
							</button>
						</div>
					)}
				</header>

				<main className="py-8">
					{showUnallocated ? (
						<UnallocatedDetail
							onBack={() => setShowUnallocated(false)}
							onEditReceipt={handleEditReceipt}
						/>
					) : selectedVendor ? (
						<VendorDetail
							vendorId={selectedVendor}
							onBack={() => setSelectedVendor(null)}
							onEditReceipt={handleEditReceipt}
						/>
					) : currentBucketId ? (
						<BucketDetail
							bucketId={currentBucketId}
							buckets={buckets}
							onBack={() => setCurrentBucketId(null)}
							onUpdateBucket={updateBucket}
							onDeleteBucket={(id) => {
								deleteBucket(id);
								setCurrentBucketId(null);
							}}
							isNameTaken={isNameTaken}
							onEditReceipt={handleEditReceipt}
						/>
					) : (
						<Dashboard
							viewMode={showVendors ? "vendors" : "buckets"}
							onSelectBucket={setCurrentBucketId}
							onSelectVendor={setSelectedVendor}
							onSelectUnallocated={() => setShowUnallocated(true)}
							onUpload={handleFileUpload}
							showEmpty={showEmpty}
							setShowEmpty={setShowEmpty}
							startDate={dateRange.start}
							endDate={dateRange.end}
							onAddBucket={addBucket}
							isNameTaken={isNameTaken}
						/>
					)}
				</main>

				<ReceiptModal
					isOpen={isModalOpen}
					onClose={handleCloseModal}
					onSave={async (data) => {
						if (editingReceipt) {
							updateReceipt({ ...data, id: editingReceipt.id });
							return true;
						} else {
							const receiptDate = new Date(data.date);
							const newValue =
								filterConfig.mode === "year"
									? String(receiptDate.getFullYear())
									: format(receiptDate, "yyyy-MM");
							const refreshDates =
								filterConfig.mode === "year"
									? {
											start: startOfYear(receiptDate),
											end: endOfYear(receiptDate),
										}
									: {
											start: startOfMonth(receiptDate),
											end: endOfMonth(receiptDate),
										};
							setFilterConfig((prev: FilterConfig) => ({
								...prev,
								value: newValue,
							}));
							try {
								await addReceipt(data, refreshDates);
								return true;
							} catch (error) {
								const message = getErrorMessage(error);
								setToast({
									kind: "error",
									message: message.includes("already exists for vendor")
										? message
										: `Failed to create receipt. ${message}`,
								});
								return false;
							}
						}
					}}
					onDelete={deleteReceipt}
					bucketSummaries={bucketSummaries}
					vendorNames={vendorNames}
					initialFile={uploadedFile}
					editingReceipt={editingReceipt}
					uploadingFile={uploadingFile}
					onFileUploadComplete={(hash: string, filename: string) => {
						console.log(`File uploaded: ${filename} with hash ${hash}`);
					}}
				/>
			</div>
		</div>
	);
};

export default App;
