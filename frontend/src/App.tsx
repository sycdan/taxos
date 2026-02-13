import React, { useState, useEffect, useMemo } from "react";
import { Plus, LayoutDashboard, ArrowLeft, LogOut, Upload } from "lucide-react";
import Dashboard from "./components/Dashboard";
import BucketDetail from "./components/BucketDetail";
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
	value: string; // "YYYY" or "YYYY-MM"
}

const App: React.FC = () => {
	const {
		buckets,
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

	// Persist filter config
	useEffect(() => {
		localStorage.setItem("taxos_filter_config", JSON.stringify(filterConfig));
	}, [filterConfig]);

	// Derive start/end dates for the rest of the app
	const dateRange = useMemo(() => {
		try {
			if (filterConfig.mode === "year") {
				const year = parseInt(filterConfig.value) || new Date().getFullYear();
				const date = new Date(year, 0, 1);
				return {
					start: startOfYear(date),
					end: endOfYear(date),
				};
			} else {
				const [year, month] = (
					filterConfig.value || format(new Date(), "yyyy-MM")
				)
					.split("-")
					.map(Number);
				const date =
					isNaN(year) || isNaN(month)
						? new Date()
						: new Date(year, month - 1, 1);
				return {
					start: startOfMonth(date),
					end: endOfMonth(date),
				};
			}
		} catch (e) {
			console.error("Date parsing failed, falling back to current month", e);
			return { start: startOfMonth(new Date()), end: endOfMonth(new Date()) };
		}
	}, [filterConfig]); // Only recalculate when filterConfig changes

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
			// If "Clear" is clicked in native picker, reset to current Year
			setFilterConfig({
				mode: "year",
				value: format(new Date(), "yyyy"),
			});
			return;
		}
		setFilterConfig((prev: FilterConfig): FilterConfig => ({ ...prev, value }));
	};

	// Calculate file hash
	const calculateFileHash = async (file: File): Promise<string> => {
		const arrayBuffer = await file.arrayBuffer();
		if (crypto && crypto.subtle) {
			const hashBuffer = await crypto.subtle.digest("SHA-256", arrayBuffer);
			const hashArray = Array.from(new Uint8Array(hashBuffer));
			return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
		} else {
			// Fallback for non-secure contexts (http)
			return sha256(arrayBuffer);
		}
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

	const navigateToDashboard = () => {
		setCurrentBucketId(null);
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
			<aside className="sidebar">
				<div className="logo mb-12">TAXOS</div>

				<nav className="flex flex-col gap-2 flex-1">
					<button
						className={`btn ${!currentBucketId ? "btn-primary" : "btn-ghost"} justify-start w-full`}
						onClick={navigateToDashboard}
					>
						<LayoutDashboard size={20} />
						<span>Receipts</span>
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
						{currentBucketId && (
							<button
								className="btn btn-ghost p-1"
								onClick={() => setCurrentBucketId(null)}
							>
								<ArrowLeft size={20} />
							</button>
						)}
						<div className="text-sm font-bold uppercase tracking-wider text-muted">
							{currentBucketId ? "Bucket Detail" : "Receipts"}
						</div>
					</div>

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

						<div className="flex gap-2">
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
									e.target.value = ""; // Reset input
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
					</div>
				</header>

				<main className="py-8">
					{currentBucketId ? (
						<BucketDetail
							bucketId={currentBucketId}
							buckets={buckets}
							onBack={() => setCurrentBucketId(null)}
							startDate={dateRange.start}
							endDate={dateRange.end}
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
							onSelectBucket={setCurrentBucketId}
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
					onSave={(data: any) => {
						if (data.id) {
							updateReceipt(data);
						} else {
							addReceipt(data);
						}
					}}
					onDelete={deleteReceipt}
					buckets={buckets}
					initialFile={uploadedFile}
					editingReceipt={editingReceipt}
					uploadingFile={uploadingFile}
					onFileUploadComplete={(hash: string, filename: string) => {
						// File upload completed, keep modal open for user to complete receipt info
						console.log(`File uploaded: ${filename} with hash ${hash}`);
					}}
				/>
			</div>
		</div>
	);
};

export default App;
