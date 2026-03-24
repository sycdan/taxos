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
import { Timestamp } from "@bufbuild/protobuf";
import type { Bucket, BucketSummary, Receipt, Vendor } from "../types";
import { client, getToken, dateToTimestamp } from "../api/client";
import { UNALLOCATED_BUCKET_ID } from "../types";

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
	addReceipt: (receipt: Omit<Receipt, "id">) => Promise<void>;
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
	// Keep a state copy so triggerRefresh (called after mutations) sees the
	// latest dates without needing to be in refreshBuckets' dep array.
	const [currentDateFilter, setCurrentDateFilter] = useState<{
		start?: Date;
		end?: Date;
	}>({});

	// Helper to convert Timestamp to ISO string
	const timestampToIso = (ts?: Timestamp) => {
		if (!ts) return new Date().toISOString();
		const tsObj = ts as unknown as { toDate?: () => Date; seconds?: number | bigint; nanos?: number };
		if (typeof tsObj.toDate === "function") return tsObj.toDate().toISOString();
		const seconds = Number(tsObj.seconds ?? 0);
		const nanos = Number(tsObj.nanos ?? 0);
		return new Date(seconds * 1000 + nanos / 1_000_000).toISOString();
	};

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

				const bucketReceipts: Receipt[] = response.receipts.map((r) => ({
					id: r.guid,
					vendor: r.vendor,
					total: r.total,
					date: timestampToIso(r.date),
					timezone: r.timezone,
					allocations: r.allocations.map((a) => ({
						bucketId: a.bucket,
						amount: a.amount,
					})),
					ref: r.vendorRef || undefined,
					notes: r.notes || undefined,
					hash: r.hash || undefined,
				}));

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

	const refreshBuckets = useCallback(
		async (startDate?: Date, endDate?: Date, force?: boolean) => {
			// Prevent concurrent requests; queue the latest dates so we can
			// re-run after the in-flight request completes.
			if (isRefreshingRef.current) {
				pendingRefreshRef.current = { start: startDate, end: endDate };
				return;
			}

			// Only refresh if dates have actually changed or it's the initial load
			// Use the ref so this check is always against the latest value,
			// even when called from a stale closure.
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

			if (!force && sameStart && sameEnd && buckets.length > 0) {
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

				// Update both the ref (immediately visible to future calls) and
				// the state (used by triggerRefresh after mutations).
				currentDateFilterRef.current = { start: startDate, end: endDate };
				setCurrentDateFilter({ start: startDate, end: endDate });

				const response = await client.getDashboard({
					months: getMonthsInRange(startDate, endDate),
				});

				const apiBuckets: Bucket[] = response.buckets.map((summary) => ({
					id: summary.guid,
					name: summary.name,
				}));

				const apiSummaries: BucketSummary[] = response.buckets.map(
					(summary) => ({
						bucket: {
							id: summary.guid,
							name: summary.name,
						},
						totalAmount: summary.totalAmount,
						receiptCount: summary.receiptCount,
					}),
				);

				const apiUnallocatedReceipts: Receipt[] =
					response.unallocatedReceipts.map((r) => ({
						id: r.guid,
						vendor: r.vendor,
						total: r.total,
						date: timestampToIso(r.date),
						timezone: r.timezone,
						allocations: r.allocations.map((a) => ({
							bucketId: a.bucket,
							amount: a.amount,
						})),
						ref: r.vendorRef || undefined,
						notes: r.notes || undefined,
						hash: r.hash || undefined,
					}));

				// Calculate unallocated portions for the pseudo-bucket summary
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
						unallocatedCount++;
					}
				}

				// If triggerRefresh fired while this fetch was in-flight, discard
				// this (now-stale) response so we don't overwrite optimistic state.
				if (mySeq !== refreshSeqRef.current) {
					return;
				}

				setBuckets(apiBuckets);
				setBucketSummaries(apiSummaries);
				setUnallocatedReceipts(apiUnallocatedReceipts);
				setVendorNames(response.vendorNames || []);
				setUnallocatedSummary({
					totalAmount: unallocatedTotal,
					receiptCount: unallocatedCount,
				});

				// If we have an active bucket that ISN'T unallocated, reload that specific bucket's receipts
				// Otherwise, show unallocated receipts (default dashboard view)
				const currentActiveBucketId = activeBucketIdRef.current;
				if (
					currentActiveBucketId &&
					currentActiveBucketId !== UNALLOCATED_BUCKET_ID &&
					startDate &&
					endDate
				) {
					void loadReceiptsForBucket(currentActiveBucketId, startDate, endDate);
				} else {
					// Default view is unallocated if no specific bucket is being loaded
					setCurrentReceiptsList(apiUnallocatedReceipts);
				}

				// Update cache
				setReceipts((prev) => {
					const updated = { ...prev };
					for (const r of apiUnallocatedReceipts) {
						updated[r.id] = r;
					}
					return updated;
				});
			} catch (error) {
				console.error("Failed to load dashboard:", error);
			} finally {
				isRefreshingRef.current = false;
				setLoading(false);
				// If a refresh was requested while we were in-flight, run it now.
				if (pendingRefreshRef.current) {
					const pending = pendingRefreshRef.current;
					pendingRefreshRef.current = null;
					void refreshBuckets(pending.start, pending.end, true);
				}
			}
		},
		// Intentionally omit currentDateFilter and activeBucketId: we read them
		// via refs so that this callback stays stable and doesn't cause the
		// Dashboard useEffect to re-fire in a loop.
		// eslint-disable-next-line react-hooks/exhaustive-deps
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

	const addReceipt = async (receipt: Omit<Receipt, "id">) => {
		try {
			const response = await client.createReceipt({
				vendor: receipt.vendor,
				total: receipt.total,
				date: dateToTimestamp(new Date(receipt.date)),
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
				date: timestampToIso(response.date),
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
			triggerRefresh();
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
				date: dateToTimestamp(new Date(receipt.date)),
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
				date: timestampToIso(response.date),
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
		// Dashboard handles the refresh which populates unallocatedReceipts
		return unallocatedReceipts;
	}, [unallocatedReceipts]);

	const refreshVendors = useCallback(async () => {
		try {
			const response = await client.listVendors({});
			const apiVendors: Vendor[] = response.vendors.map((v) => ({
				id: v.guid,
				name: v.name,
			}));
			setVendors(apiVendors);
		} catch (error) {
			console.error("Failed to load vendors:", error);
		}
	}, []);

	const updateVendor = useCallback(async (id: string, name: string): Promise<Vendor | null> => {
		try {
			const response = await client.updateVendor({ guid: id, name });
			const updated: Vendor = { id: response.guid, name: response.name };
			setVendors((prev) => prev.map((v) => (v.id === id ? updated : v)));
			return updated;
		} catch (error) {
			console.error("Failed to update vendor:", error);
			return null;
		}
	}, []);

	return (
		<TaxosContext.Provider
			value={{
				buckets,
				bucketSummaries,
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
