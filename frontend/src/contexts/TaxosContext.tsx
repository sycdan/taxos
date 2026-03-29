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
import { UNALLOCATED_BUCKET_ID } from "../types";

const slugify = (text: string) => {
	return text
		.toLowerCase()
		.trim()
		.replace(/[^\w\s-]/g, "")
		.replace(/[\s_-]+/g, "-")
		.replace(/^-+|-+$/g, "");
};

const isGuid = (value: string) => /^[0-9a-f]{32}$/i.test(value);

interface TaxosContextType {
	buckets: Bucket[];
	bucketSummaries: BucketSummary[];
	vendorSummaries: import("../types").VendorSummary[];
	unallocatedSummary: { totalAmount: number; receiptCount: number };
	receipts: Record<string, Receipt>;
	unallocatedReceipts: Receipt[];
	currentReceiptsList: Receipt[];
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
	loadReceiptsForBucket: (
		bucketId: string,
		startDate: Date,
		endDate: Date,
	) => Promise<Receipt[]>;
	loadReceiptsForVendor: (
		vendor: string,
		startDate: Date,
		endDate: Date,
	) => Promise<Receipt[]>;
	getUnallocatedReceipts: (
		startDate: Date,
		endDate: Date,
	) => Promise<Receipt[]>;
	activeBucketId: string | null;
	setActiveBucketId: (id: string | null) => void;
	refreshVendors: () => Promise<void>;
	updateVendor: (id: string, name: string) => Promise<Vendor | null>;
}

const TaxosContext = createContext<TaxosContextType | undefined>(undefined);

export const TaxosProvider: React.FC<{ children: ReactNode }> = ({
	children,
}) => {
	const [buckets, setBuckets] = useState<Bucket[]>([]);
	const [bucketSummaries, setBucketSummaries] = useState<BucketSummary[]>([]);
	const [vendorSummaries, setVendorSummaries] = useState<
		import("../types").VendorSummary[]
	>([]);
	const [unallocatedSummary, setUnallocatedSummary] = useState<{
		totalAmount: number;
		receiptCount: number;
	}>({ totalAmount: 0, receiptCount: 0 });
	const [receipts, setReceipts] = useState<Record<string, Receipt>>({});
	const [unallocatedReceipts, setUnallocatedReceipts] = useState<Receipt[]>([]);
	const [currentReceiptsList, setCurrentReceiptsList] = useState<Receipt[]>([]);
	const [vendorNames, setVendorNames] = useState<string[]>([]);
	const [vendors, setVendors] = useState<Vendor[]>([]);
	const [activeBucketId, setActiveBucketId] = useState<string | null>(null);

	// Track receipt hashes for O(1) duplicate detection
	const receiptHashes = useMemo(() => {
		const hashes = new Set<string>();
		Object.values(receipts).forEach((r) => {
			if (r.hash) hashes.add(r.hash);
		});
		return hashes;
	}, [receipts]);
	const [loading, setLoading] = useState(true);
	const [authenticated] = useState(!!getToken());
	// Use refs for date filter and activeBucketId so refreshBuckets doesn't
	// recreate itself on every call (which would otherwise cause loop issues).
	const currentDateFilterRef = useRef<{ start?: Date; end?: Date }>({});
	const activeBucketIdRef = useRef<string | null>(null);
	const isRefreshingRef = useRef(false);
	// Holds dates for a refresh that was requested while one was already in-flight.
	const pendingRefreshRef = useRef<{ start?: Date; end?: Date } | null>(null);
	// Monotonically-incrementing counter. triggerRefresh bumps it before firing
	// a new fetch so any in-flight (pre-mutation) response can detect it is stale.
	const refreshSeqRef = useRef(0);

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

	const loadReceiptsForBucket = useCallback(
		async (
			bucketId: string,
			startDate: Date,
			endDate: Date,
		): Promise<Receipt[]> => {
			try {
				const response = await client.listReceipts({
					bucket: bucketId,
					months: getMonthsInRange(startDate, endDate),
				});

				const bucketReceipts: Receipt[] = response.receipts.map(
					(r: MappedReceipt) => ({
						id: r.guid,
						vendor: r.vendor,
						total: r.total,
						date: r.date,
						timezone: r.timezone,
						allocations: r.allocations.map((a) => ({
							bucketId: a.bucket,
							amount: a.amount,
						})),
						ref: r.vendorRef || undefined,
						notes: r.notes || undefined,
						hash: r.hash || undefined,
					}),
				);

				// Update source of truth for current view
				setCurrentReceiptsList(bucketReceipts);

				// Update cache
				setReceipts((prev) => {
					const updated = { ...prev };
					for (const receipt of bucketReceipts) {
						updated[receipt.id] = receipt;
					}
					return updated;
				});

				return bucketReceipts;
			} catch (error) {
				console.error("Failed to load receipts for bucket:", error);
				return [];
			}
		},
		[],
	);

	const loadReceiptsForVendor = useCallback(
		async (
			vendor: string,
			startDate: Date,
			endDate: Date,
		): Promise<Receipt[]> => {
			try {
				if (!isGuid(vendor)) {
					console.warn(
						"Skipping vendor receipt query with non-GUID vendor id",
						{
							vendor,
						},
					);
					setCurrentReceiptsList([]);
					return [];
				}

				const response = await client.listReceipts({
					vendor: vendor,
					months: getMonthsInRange(startDate, endDate),
				});

				const vendorReceipts: Receipt[] = response.receipts.map(
					(r: MappedReceipt) => ({
						id: r.guid,
						vendor: r.vendor,
						total: r.total,
						date: r.date,
						timezone: r.timezone,
						allocations: r.allocations.map((a) => ({
							bucketId: a.bucket,
							amount: a.amount,
						})),
						ref: r.vendorRef || undefined,
						notes: r.notes || undefined,
						hash: r.hash || undefined,
					}),
				);

				// Update source of truth for current view
				setCurrentReceiptsList(vendorReceipts);

				// Update cache
				setReceipts((prev) => {
					const updated = { ...prev };
					for (const receipt of vendorReceipts) {
						updated[receipt.id] = receipt;
					}
					return updated;
				});

				return vendorReceipts;
			} catch (error) {
				console.error("Failed to load receipts for vendor:", error);
				return [];
			}
		},
		[],
	);

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

				const [bucketsResponse, allReceiptsResponse, vendorsResponse] =
					await Promise.all([
						client.listBuckets(),
						client.listReceipts({ months }),
						client.listVendors(),
					]);

				const apiBuckets: Bucket[] = bucketsResponse.buckets.map((bucket) => ({
					id: bucket.guid,
					name: bucket.name,
				}));
				const apiVendors: Vendor[] = vendorsResponse.vendors.map((vendor) => ({
					id: vendor.guid,
					name: vendor.name,
				}));

				const allReceipts: Receipt[] = allReceiptsResponse.receipts.map(
					(r: MappedReceipt) => ({
						id: r.guid,
						vendor: r.vendor,
						total: r.total,
						date: r.date,
						timezone: r.timezone,
						allocations: r.allocations.map((a) => ({
							bucketId: a.bucket,
							amount: a.amount,
						})),
						ref: r.vendorRef || undefined,
						notes: r.notes || undefined,
						hash: r.hash || undefined,
					}),
				);

				const bucketTotals = new Map<
					string,
					{ total: number; receipts: Set<string> }
				>();
				for (const bucket of apiBuckets) {
					bucketTotals.set(bucket.id, {
						total: 0,
						receipts: new Set<string>(),
					});
				}

				const apiUnallocatedReceipts: Receipt[] = [];

				for (const receipt of allReceipts) {
					let allocatedAmount = 0;
					for (const allocation of receipt.allocations) {
						allocatedAmount += allocation.amount;
						const bucketEntry = bucketTotals.get(allocation.bucketId);
						if (bucketEntry) {
							bucketEntry.total += allocation.amount;
							bucketEntry.receipts.add(receipt.id);
						}
					}

					if (receipt.total - allocatedAmount > 0) {
						apiUnallocatedReceipts.push(receipt);
					}
				}

				const apiSummaries: BucketSummary[] = apiBuckets.map((bucket) => {
					const totals = bucketTotals.get(bucket.id);
					return {
						bucket,
						totalAmount: totals?.total ?? 0,
						receiptCount: totals?.receipts.size ?? 0,
					};
				});

				let unallocatedTotal = 0;
				let unallocatedCount = 0;

				for (const r of apiUnallocatedReceipts) {
					const allocatedAmount = r.allocations.reduce(
						(sum, a) => sum + a.amount,
						0,
					);
					const unallocatedAmount = r.total - allocatedAmount;
					if (unallocatedAmount > 0) {
						unallocatedTotal += unallocatedAmount;
						unallocatedCount += 1;
					}
				}

				const vendorIdsByName = new Map(
					apiVendors.map((vendor) => [vendor.name, vendor.id]),
				);
				const vendorSummaryMap = new Map<
					string,
					import("../types").VendorSummary
				>();

				for (const vendor of apiVendors) {
					vendorSummaryMap.set(vendor.id, {
						vendor,
						totalAmount: 0,
						receiptCount: 0,
					});
				}

				for (const receipt of allReceipts) {
					const vendorId =
						vendorIdsByName.get(receipt.vendor) ?? receipt.vendor;
					const existing = vendorSummaryMap.get(vendorId) ?? {
						vendor: {
							id: vendorId,
							name: receipt.vendor,
						},
						totalAmount: 0,
						receiptCount: 0,
					};

					existing.totalAmount += receipt.total;
					existing.receiptCount += 1;
					vendorSummaryMap.set(vendorId, existing);
				}

				const apiVendorSummaries = Array.from(vendorSummaryMap.values());

				if (mySeq !== refreshSeqRef.current) {
					return;
				}

				setBuckets(apiBuckets);
				setBucketSummaries(apiSummaries);
				setVendorSummaries(apiVendorSummaries);
				setUnallocatedReceipts(apiUnallocatedReceipts);
				setVendorNames(apiVendors.map((vendor) => vendor.name));
				setVendors(apiVendors);
				setUnallocatedSummary({
					totalAmount: unallocatedTotal,
					receiptCount: unallocatedCount,
				});

				const currentActiveBucketId = activeBucketIdRef.current;
				if (
					currentActiveBucketId &&
					currentActiveBucketId !== UNALLOCATED_BUCKET_ID &&
					startDate &&
					endDate
				) {
					void loadReceiptsForBucket(currentActiveBucketId, startDate, endDate);
				} else {
					setCurrentReceiptsList(apiUnallocatedReceipts);
				}

				setReceipts((prev) => {
					const updated = { ...prev };
					for (const r of allReceipts) {
						updated[r.id] = r;
					}
					return updated;
				});
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
		// Intentionally omit activeBucketId and bucket arrays; they are read via refs/state updates.
		[authenticated, loadReceiptsForBucket],
	);

	// Don't load buckets on mount - let Dashboard call refreshBuckets with date filter
	useEffect(() => {
		if (!authenticated) {
			setLoading(false);
		} else {
			setLoading(false);
		}
	}, [authenticated]);

	const triggerRefresh = useCallback(() => {
		// Read dates from the ref (updated synchronously inside refreshBuckets)
		// rather than from state, which may lag by one render cycle.
		const { start, end } = currentDateFilterRef.current;
		if (start || end) {
			// Bump seq so any in-flight (pre-mutation) response is discarded.
			refreshSeqRef.current += 1;
			void refreshBuckets(start, end, true);
		}
	}, [refreshBuckets]);

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
			// Optimistically add an empty summary so the bucket chip appears in
			// the receipt modal immediately, without waiting for triggerRefresh.
			const newSummary: BucketSummary = {
				bucket: newBucket,
				totalAmount: 0,
				receiptCount: 0,
			};
			setBuckets((prev) => [...prev, newBucket]);
			setBucketSummaries((prev) => [...prev, newSummary]);
			triggerRefresh();
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
			setBuckets((prev) => prev.map((b) => (b.id === id ? { ...b, name } : b)));
			setBucketSummaries((prev) =>
				prev.map((s) =>
					s.bucket.id === id ? { ...s, bucket: { ...s.bucket, name } } : s,
				),
			);
			return true;
		} catch (error) {
			console.error("Failed to update bucket:", error);
			return false;
		}
	};

	const deleteBucket = async (id: string) => {
		try {
			await client.deleteBucket({ guid: id });
			setBuckets((prev) => prev.filter((b) => b.id !== id));
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
			triggerRefresh();
		} catch (error) {
			console.error("Failed to delete bucket:", error);
		}
	};

	const addReceipt = async (
		receipt: Omit<Receipt, "id">,
		refreshDates?: { start: Date; end: Date },
	) => {
		try {
			const response = await client.createReceipt({
				vendor: receipt.vendor,
				total: receipt.total,
				date: new Date(receipt.date),
				timezone: receipt.timezone,
				allocations: receipt.allocations.map((a) => ({
					bucket: a.bucketId,
					amount: a.amount,
				})),
				vendorRef: receipt.ref || "",
				notes: receipt.notes || "",
				hash: receipt.hash || "",
			});

			const createdReceipt: Receipt = {
				id: response.guid,
				vendor: response.vendor,
				total: response.total,
				date: response.date,
				timezone: response.timezone,
				allocations: response.allocations.map((a) => ({
					bucketId: a.bucket,
					amount: a.amount,
				})),
				ref: response.vendorRef || undefined,
				notes: response.notes || undefined,
				hash: response.hash || undefined,
			};

			if (createdReceipt.hash && receiptHashes.has(createdReceipt.hash)) {
				console.warn(
					"Duplicate receipt detected, skipping:",
					createdReceipt.vendor,
				);
				return;
			}
			setReceipts((prev) => ({ ...prev, [createdReceipt.id]: createdReceipt }));
			if (refreshDates) {
				refreshSeqRef.current += 1;
				void refreshBuckets(refreshDates.start, refreshDates.end, true);
			} else {
				triggerRefresh();
			}
		} catch (error) {
			console.error("Failed to create receipt:", error);
		}
	};

	const updateReceipt = async (receipt: Receipt) => {
		// Save previous state for rollback
		const previousReceipt = receipts[receipt.id];

		// Optimistically update local state
		setReceipts((prev) => ({ ...prev, [receipt.id]: receipt }));

		try {
			const response = await client.updateReceipt({
				guid: receipt.id,
				vendor: receipt.vendor,
				total: receipt.total,
				date: new Date(receipt.date),
				timezone: receipt.timezone,
				allocations: receipt.allocations.map((a) => ({
					bucket: a.bucketId,
					amount: a.amount,
				})),
				vendorRef: receipt.ref || "",
				notes: receipt.notes || "",
				hash: receipt.hash || "",
			});

			const updatedReceipt: Receipt = {
				id: response.guid,
				vendor: response.vendor,
				total: response.total,
				date: response.date,
				timezone: response.timezone,
				allocations: response.allocations.map((a) => ({
					bucketId: a.bucket,
					amount: a.amount,
				})),
				ref: response.vendorRef || "",
				notes: response.notes || "",
				hash: response.hash || "",
			};

			setReceipts((prev) => ({ ...prev, [updatedReceipt.id]: updatedReceipt }));
			triggerRefresh();
		} catch (error) {
			console.error("Failed to update receipt:", error);
			// Revert optimistic update
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
			triggerRefresh();
		} catch (error) {
			console.error("Failed to delete receipt:", error);
		}
	};

	const getUnallocatedReceipts = useCallback(async (): Promise<Receipt[]> => {
		// refreshBuckets populates unallocatedReceipts for the active date range
		return unallocatedReceipts;
	}, [unallocatedReceipts]);

	const refreshVendors = useCallback(async () => {
		try {
			const response = await client.listVendors();
			const apiVendors: Vendor[] = response.vendors.map((v) => ({
				id: v.guid,
				name: v.name,
			}));
			setVendors(apiVendors);
		} catch (error) {
			console.error("Failed to load vendors:", error);
		}
	}, []);

	const updateVendor = useCallback(
		async (id: string, name: string): Promise<Vendor | null> => {
			try {
				const response = await client.updateVendor({ guid: id, name });
				const updated: Vendor = { id: response.guid, name: response.name };
				setVendors((prev) => prev.map((v) => (v.id === id ? updated : v)));
				await refreshBuckets(
					currentDateFilterRef.current.start,
					currentDateFilterRef.current.end,
					true,
				);
				return updated;
			} catch (error) {
				console.error("Failed to update vendor:", error);
				return null;
			}
		},
		[refreshBuckets],
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
				currentReceiptsList,
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
				loadReceiptsForBucket,
				loadReceiptsForVendor,
				getUnallocatedReceipts,
				activeBucketId,
				setActiveBucketId,
				refreshVendors,
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
