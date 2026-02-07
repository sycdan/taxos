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

export const setToken = (token: string) => {
  localStorage.setItem("taxos_token", token);
  // Create a new client to pick up the new token
  window.location.reload();
};

export const getToken = () => localStorage.getItem("taxos_token");

export const clearToken = () => {
  localStorage.removeItem("taxos_token");
  window.location.reload();
};
