import React, {
	createContext,
	useContext,
	useState,
	useEffect,
	useCallback,
	useMemo,
	useRef,
	type ReactNode,
} from "react";
import type { Bucket, BucketSummary, Receipt, Vendor } from "../types";
import { client, getToken, type MappedReceipt } from "../api/client";

const slugify = (text: string) => {
	return text
		.toLowerCase()
		.trim()
		.replace(/[^\w\s-]/g, "")
		.replace(/[\s_-]+/g, "-")
		.replace(/^-+|-+$/g, "");
};

interface TaxosContextType {
	buckets: Bucket[];
	bucketSummaries: BucketSummary[];
	vendorSummaries: import("../types").VendorSummary[];
	unallocatedSummary: { totalAmount: number; receiptCount: number };
	receipts: Record<string, Receipt>;
	unallocatedReceipts: Receipt[];
	vendorNames: string[];
	vendors: Vendor[];
	loading: boolean;
	authenticated: boolean;
	isNameTaken: (name: string, excludeId?: string) => boolean;
	addBucket: (name: string) => Promise<boolean>;
	updateBucket: (id: string, name: string) => Promise<boolean>;
	deleteBucket: (id: string) => Promise<void>;
	addReceipt: (
		receipt: Omit<Receipt, "id">,
		refreshDates?: { start: Date; end: Date },
	) => Promise<void>;
	updateReceipt: (receipt: Receipt) => Promise<void>;
	deleteReceipt: (id: string) => Promise<void>;
	refreshBuckets: (
		startDate?: Date,
		endDate?: Date,
		force?: boolean,
	) => Promise<void>;
	activeBucketId: string | null;
	setActiveBucketId: (id: string | null) => void;
	updateVendor: (id: string, name: string) => Promise<Vendor | null>;
}

const TaxosContext = createContext<TaxosContextType | undefined>(undefined);

export const TaxosProvider: React.FC<{ children: ReactNode }> = ({
	children,
}) => {
	const [buckets, setBuckets] = useState<Bucket[]>([]);
	const [vendors, setVendors] = useState<Vendor[]>([]);
	const [receipts, setReceipts] = useState<Record<string, Receipt>>({});
	const [activeBucketId, setActiveBucketId] = useState<string | null>(null);
	const [loading, setLoading] = useState(true);
	const [authenticated] = useState(!!getToken());

	// Refs so stable callbacks can read current values without being in deps
	const bucketsRef = useRef<Bucket[]>([]);
	const vendorsRef = useRef<Vendor[]>([]);
	const hasLoadedStaticDataRef = useRef(false);
	const currentDateFilterRef = useRef<{ start?: Date; end?: Date }>({});
	const isRefreshingRef = useRef(false);
	const pendingRefreshRef = useRef<{ start?: Date; end?: Date } | null>(null);
	const refreshSeqRef = useRef(0);

	// Summaries are derived from receipts+buckets+vendors — no separate state needed
	const bucketSummaries = useMemo<BucketSummary[]>(() => {
		const bucketTotals = new Map<
			string,
			{ total: number; receipts: Set<string> }
		>();
		for (const bucket of buckets) {
			bucketTotals.set(bucket.id, { total: 0, receipts: new Set() });
		}
		for (const receipt of Object.values(receipts)) {
			for (const allocation of receipt.allocations) {
				const entry = bucketTotals.get(allocation.bucketId);
				if (entry) {
					entry.total += allocation.amount;
					entry.receipts.add(receipt.id);
				}
			}
		}
		return buckets.map((bucket) => {
			const totals = bucketTotals.get(bucket.id);
			return {
				bucket,
				totalAmount: totals?.total ?? 0,
				receiptCount: totals?.receipts.size ?? 0,
			};
		});
	}, [buckets, receipts]);

	const unallocatedReceipts = useMemo<Receipt[]>(() => {
		return Object.values(receipts).filter((receipt) => {
			const allocatedAmount = receipt.allocations.reduce(
				(sum, a) => sum + a.amount,
				0,
			);
			return receipt.total - allocatedAmount > 0;
		});
	}, [receipts]);

	const unallocatedSummary = useMemo(() => {
		let totalAmount = 0;
		let receiptCount = 0;
		for (const r of unallocatedReceipts) {
			const allocatedAmount = r.allocations.reduce((sum, a) => sum + a.amount, 0);
			totalAmount += r.total - allocatedAmount;
			receiptCount += 1;
		}
		return { totalAmount, receiptCount };
	}, [unallocatedReceipts]);

	const vendorSummaries = useMemo<import("../types").VendorSummary[]>(() => {
		const vendorSummaryMap = new Map<string, import("../types").VendorSummary>();
		for (const vendor of vendors) {
			vendorSummaryMap.set(vendor.id, {
				vendor,
				totalAmount: 0,
				receiptCount: 0,
			});
		}
		for (const receipt of Object.values(receipts)) {
			const vendor = vendors.find((v) => v.name === receipt.vendor);
			const vendorId = vendor?.id ?? receipt.vendor;
			const existing = vendorSummaryMap.get(vendorId) ?? {
				vendor: { id: vendorId, name: receipt.vendor },
				totalAmount: 0,
				receiptCount: 0,
			};
			existing.totalAmount += receipt.total;
			existing.receiptCount += 1;
			vendorSummaryMap.set(vendorId, existing);
		}
		return Array.from(vendorSummaryMap.values());
	}, [vendors, receipts]);

	const vendorNames = useMemo(() => vendors.map((v) => v.name), [vendors]);

	// Track receipt file hashes for O(1) duplicate detection
	const receiptHashes = useMemo(() => {
		const hashes = new Set<string>();
		Object.values(receipts).forEach((r) => {
			r.fileAttachments?.forEach((fa) => hashes.add(fa.hash));
		});
		return hashes;
	}, [receipts]);

	// Helper to generate "yyyy-mm" strings for a range
	const getMonthsInRange = (start?: Date, end?: Date): string[] => {
		if (!start || !end) return [];
		const months: string[] = [];
		const current = new Date(start.getFullYear(), start.getMonth(), 1);
		const last = new Date(end.getFullYear(), end.getMonth(), 1);

		while (current <= last) {
			const year = current.getFullYear();
			const month = String(current.getMonth() + 1).padStart(2, "0");
			months.push(`${year}-${month}`);
			current.setMonth(current.getMonth() + 1);
		}
		return months;
	};

	// Loads receipts for the given date range. Buckets and vendors are loaded
	// once on first call and then reused from refs — never re-fetched.
	const refreshBuckets = useCallback(
		async (startDate?: Date, endDate?: Date, force?: boolean) => {
			if (isRefreshingRef.current) {
				pendingRefreshRef.current = { start: startDate, end: endDate };
				return;
			}

			const currentFilter = currentDateFilterRef.current;
			const sameStart =
				(!startDate && !currentFilter.start) ||
				(startDate &&
					currentFilter.start &&
					startDate.getTime() === currentFilter.start.getTime());
			const sameEnd =
				(!endDate && !currentFilter.end) ||
				(endDate &&
					currentFilter.end &&
					endDate.getTime() === currentFilter.end.getTime());

			if (!force && sameStart && sameEnd) {
				return;
			}

			isRefreshingRef.current = true;
			const mySeq = refreshSeqRef.current;
			try {
				setLoading(true);
				if (!authenticated) {
					setLoading(false);
					return;
				}

				currentDateFilterRef.current = { start: startDate, end: endDate };
				const months = getMonthsInRange(startDate, endDate);

				let apiBuckets: Bucket[];
				let apiVendors: Vendor[];

				if (!hasLoadedStaticDataRef.current) {
					// First load: fetch buckets and vendors from the server
					const [bucketsResponse, vendorsResponse] = await Promise.all([
						client.listBuckets(),
						client.listVendors(),
					]);
					apiBuckets = bucketsResponse.buckets.map((b) => ({
						id: b.guid,
						name: b.name,
					}));
					apiVendors = vendorsResponse.vendors.map((v) => ({
						id: v.guid,
						name: v.name,
					}));
					bucketsRef.current = apiBuckets;
					vendorsRef.current = apiVendors;
					hasLoadedStaticDataRef.current = true;
				} else {
					// Subsequent loads: reuse cached static data via refs so the
					// stable useCallback closure doesn't capture stale state values.
					apiBuckets = bucketsRef.current;
					apiVendors = vendorsRef.current;
				}

				const allReceiptsResponse = await client.listReceipts({ months });

				const allReceipts: Receipt[] = allReceiptsResponse.receipts.map(
					(r: MappedReceipt) => ({
						id: r.guid,
						vendor:
							apiVendors.find((v) => v.id === r.vendorGuid)?.name ?? r.vendorGuid,
						total: r.total,
						date: r.date,
						timezone: r.timezone,
						allocations: r.allocations.map((a) => ({
							bucketId: a.bucket,
							amount: a.amount,
						})),
						ref: r.vendorRef || undefined,
						notes: r.notes || undefined,
						fileAttachments: r.fileAttachments?.length ? r.fileAttachments : undefined,
					}),
				);

				if (mySeq !== refreshSeqRef.current) {
					return;
				}

				setBuckets((prev) => {
					bucketsRef.current = apiBuckets;
					if (
						prev.length === apiBuckets.length &&
						prev.every((b, i) => b.id === apiBuckets[i]?.id && b.name === apiBuckets[i]?.name)
					) {
						return prev;
					}
					return apiBuckets;
				});
				setVendors((prev) => {
					vendorsRef.current = apiVendors;
					// Only update state if the list actually changed to avoid churn
					if (
						prev.length === apiVendors.length &&
						prev.every((v, i) => v.id === apiVendors[i]?.id && v.name === apiVendors[i]?.name)
					) {
						return prev;
					}
					return apiVendors;
				});

				const receiptMap: Record<string, Receipt> = {};
				for (const r of allReceipts) {
					receiptMap[r.id] = r;
				}
				setReceipts(receiptMap);
			} catch (error) {
				console.error("Failed to refresh receipts and summaries:", error);
			} finally {
				isRefreshingRef.current = false;
				setLoading(false);
				if (pendingRefreshRef.current) {
					const pending = pendingRefreshRef.current;
					pendingRefreshRef.current = null;
					void refreshBuckets(pending.start, pending.end, true);
				}
			}
		},
		// authenticated is stable (never changes after mount). All mutable state
		// (buckets, vendors) is accessed via refs so this callback never needs
		// to be recreated.
		[authenticated],
	);

	useEffect(() => {
		if (!authenticated) {
			setLoading(false);
		} else {
			setLoading(false);
		}
	}, [authenticated]);

	const isNameTaken = (name: string, excludeId?: string) => {
		const slug = slugify(name);
		return buckets.some((b) => b.id !== excludeId && slugify(b.name) === slug);
	};

	const addBucket = async (name: string) => {
		if (isNameTaken(name)) return false;

		try {
			const response = await client.createBucket({ name });
			const newBucket: Bucket = {
				id: response.guid,
				name: response.name,
			};
			setBuckets((prev) => {
				const updated = [...prev, newBucket];
				bucketsRef.current = updated;
				return updated;
			});
			return true;
		} catch (error) {
			console.error("Failed to create bucket:", error);
			return false;
		}
	};

	const updateBucket = async (id: string, name: string) => {
		if (isNameTaken(name, id)) return false;

		try {
			await client.updateBucket({ guid: id, name });
			setBuckets((prev) => {
				const updated = prev.map((b) => (b.id === id ? { ...b, name } : b));
				bucketsRef.current = updated;
				return updated;
			});
			return true;
		} catch (error) {
			console.error("Failed to update bucket:", error);
			return false;
		}
	};

	const deleteBucket = async (id: string) => {
		try {
			await client.deleteBucket({ guid: id });
			setBuckets((prev) => {
				const updated = prev.filter((b) => b.id !== id);
				bucketsRef.current = updated;
				return updated;
			});
			setReceipts((prev) => {
				const updated = { ...prev };
				for (const key in updated) {
					updated[key] = {
						...updated[key],
						allocations: updated[key].allocations.filter(
							(a) => a.bucketId !== id,
						),
					};
				}
				return updated;
			});
		} catch (error) {
			console.error("Failed to delete bucket:", error);
		}
	};

	const addReceipt = async (
		receipt: Omit<Receipt, "id">,
		// refreshDates kept for API compat — no longer triggers a full reload.
		// The date-filter change in App.tsx triggers refreshBuckets if needed.
		// eslint-disable-next-line @typescript-eslint/no-unused-vars
		_refreshDates?: { start: Date; end: Date },
	) => {
		try {
			const upsertedVendor = await client.upsertVendor({
				name: receipt.vendor,
			});
			const response = await client.createReceipt({
				vendor: upsertedVendor.guid,
				total: receipt.total,
				date: new Date(receipt.date),
				timezone: receipt.timezone,
				allocations: receipt.allocations.map((a) => ({
					bucket: a.bucketId,
					amount: a.amount,
				})),
				vendorRef: receipt.ref || "",
				notes: receipt.notes || "",
				fileAttachments: receipt.fileAttachments,
			});

			const createdReceipt: Receipt = {
				id: response.guid,
				vendor: receipt.vendor,
				total: response.total,
				date: response.date,
				timezone: response.timezone,
				allocations: response.allocations.map((a) => ({
					bucketId: a.bucket,
					amount: a.amount,
				})),
				ref: response.vendorRef || undefined,
				notes: response.notes || undefined,
				fileAttachments: response.fileAttachments?.length ? response.fileAttachments : undefined,
			};

			if (createdReceipt.fileAttachments?.[0]?.hash && receiptHashes.has(createdReceipt.fileAttachments[0].hash)) {
				console.warn(
					"Duplicate receipt detected, skipping:",
					createdReceipt.vendor,
				);
				return;
			}

			// Patch new vendor into list if it wasn't there before
			setVendors((prev) => {
				if (prev.some((v) => v.id === upsertedVendor.guid)) return prev;
				const updated = [
					...prev,
					{ id: upsertedVendor.guid, name: receipt.vendor },
				];
				vendorsRef.current = updated;
				return updated;
			});

			setReceipts((prev) => ({ ...prev, [createdReceipt.id]: createdReceipt }));
		} catch (error) {
			console.error("Failed to create receipt:", error);
			throw error;
		}
	};

	const updateReceipt = async (receipt: Receipt) => {
		const previousReceipt = receipts[receipt.id];

		// Optimistically update local state
		setReceipts((prev) => ({ ...prev, [receipt.id]: receipt }));

		try {
			const upsertedVendor = await client.upsertVendor({
				name: receipt.vendor,
			});
			const response = await client.updateReceipt({
				guid: receipt.id,
				vendor: upsertedVendor.guid,
				total: receipt.total,
				date: new Date(receipt.date),
				timezone: receipt.timezone,
				allocations: receipt.allocations.map((a) => ({
					bucket: a.bucketId,
					amount: a.amount,
				})),
				vendorRef: receipt.ref || "",
				notes: receipt.notes || "",
				fileAttachments: receipt.fileAttachments,
			});

			const updatedReceipt: Receipt = {
				id: response.guid,
				vendor: receipt.vendor,
				total: response.total,
				date: response.date,
				timezone: response.timezone,
				allocations: response.allocations.map((a) => ({
					bucketId: a.bucket,
					amount: a.amount,
				})),
				ref: response.vendorRef || "",
				notes: response.notes || "",
				fileAttachments: response.fileAttachments ?? [],
			};

			setReceipts((prev) => ({ ...prev, [updatedReceipt.id]: updatedReceipt }));
		} catch (error) {
			console.error("Failed to update receipt:", error);
			if (previousReceipt) {
				setReceipts((prev) => ({ ...prev, [receipt.id]: previousReceipt }));
			}
		}
	};

	const deleteReceipt = async (id: string) => {
		try {
			await client.deleteReceipt({ guid: id });
			setReceipts((prev) => {
				const next = { ...prev };
				delete next[id];
				return next;
			});
		} catch (error) {
			console.error("Failed to delete receipt:", error);
		}
	};

	const updateVendor = useCallback(
		async (id: string, name: string): Promise<Vendor | null> => {
			try {
				const oldName =
					vendorsRef.current.find((v) => v.id === id)?.name ?? id;
				const response = await client.updateVendor({ guid: id, name });
				const updated: Vendor = { id: response.guid, name: response.name };

				setVendors((prev) => {
					const newVendors = prev.map((v) => (v.id === id ? updated : v));
					vendorsRef.current = newVendors;
					return newVendors;
				});

				// Patch vendor name in all receipts that reference the old name
				if (oldName !== name) {
					setReceipts((prev) => {
						const next = { ...prev };
						for (const [rid, receipt] of Object.entries(next)) {
							if (receipt.vendor === oldName) {
								next[rid] = { ...receipt, vendor: name };
							}
						}
						return next;
					});
				}

				return updated;
			} catch (error) {
				console.error("Failed to update vendor:", error);
				return null;
			}
		},
		[],
	);

	return (
		<TaxosContext.Provider
			value={{
				buckets,
				bucketSummaries,
				vendorSummaries,
				unallocatedSummary,
				receipts,
				unallocatedReceipts,
				vendorNames,
				vendors,
				loading,
				authenticated,
				isNameTaken,
				addBucket,
				updateBucket,
				deleteBucket,
				addReceipt,
				updateReceipt,
				deleteReceipt,
				refreshBuckets,
				activeBucketId,
				setActiveBucketId,
				updateVendor,
			}}
		>
			{children}
		</TaxosContext.Provider>
	);
};

// eslint-disable-next-line react-refresh/only-export-components
export const useTaxos = () => {
	const context = useContext(TaxosContext);
	if (context === undefined) {
		throw new Error("useTaxos must be used within a TaxosProvider");
	}
	return context;
};
