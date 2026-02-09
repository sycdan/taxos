import { createClient, type Interceptor, Code } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";
import { TaxosApi } from "./v1/taxos_service_connect";

const baseUrl = import.meta.env.VITE_GRPC_API_URL || "http://localhost:8080";

const logoutOnUnauthorized = () => {
  localStorage.removeItem("taxos_token");
  window.location.href = "/";
};

// Create an interceptor that adds the token to requests
const tokenInterceptor: Interceptor = (next) => async (req) => {
  const token = localStorage.getItem("taxos_token");
  if (token) {
    req.header.set("Authorization", `Bearer ${token}`);
  }

  try {
    return await next(req);
  } catch (error: unknown) {
    const err = error as { code?: Code; status?: number } | null;
    // Check if it's a 401/Unauthenticated error
    if (err?.code === Code.Unauthenticated || err?.status === 401) {
      logoutOnUnauthorized();
    }
    throw error;
  }
};

export const client = createClient(
  TaxosApi,
  createConnectTransport({
    baseUrl,
    interceptors: [tokenInterceptor],
  })
);

// Helper to convert Date to Timestamp
export const dateToTimestamp = (date: Date) => {
  const seconds = BigInt(Math.floor(date.getTime() / 1000));
  const nanos = (date.getTime() % 1000) * 1_000_000;
  return { seconds, nanos };
};

export const setToken = (token: string) => {
  localStorage.setItem("taxos_token", token);
  // Create a new client to pick up the new token
  window.location.reload();
};

// Upload a receipt file
export const uploadReceiptFile = async (
  file: File,
  hash: string,
  onProgress?: (progress: number) => void
) => {
  try {
    // Convert file to Uint8Array for protobuf bytes field
    const fileBuffer = await file.arrayBuffer();
    const fileBytes = new Uint8Array(fileBuffer);

    // Simulate progress for the encoding step
    onProgress?.(25);

    const response = await client.uploadReceiptFile({
      fileHash: hash,
      filename: file.name,
      fileData: fileBytes,
    });

    onProgress?.(100);

    return {
      alreadyExists: response.alreadyExists,
      fileInfo: response.fileInfo ? {
        fileHash: response.fileInfo.fileHash,
        filename: response.fileInfo.filename,
        filePath: response.fileInfo.filePath,
        fileSize: Number(response.fileInfo.fileSize),
        uploadedAt: response.fileInfo.uploadedAt,
      } : undefined,
    };
  } catch (error) {
    onProgress?.(0);
    throw error;
  }
};

export const getToken = () => localStorage.getItem("taxos_token");

export const clearToken = () => {
  localStorage.removeItem("taxos_token");
  window.location.reload();
};
