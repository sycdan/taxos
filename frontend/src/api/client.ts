import { createPromiseClient } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";
import { TaxosApi } from "./v1/taxos_service_connect";

const baseUrl = import.meta.env.VITE_GRPC_API_URL || "http://localhost:8080";

// Create an interceptor that adds the token to requests
const tokenInterceptor = (next: any) => async (req: any) => {
  const token = localStorage.getItem("taxos_token");
  if (token) {
    req.header.set("Authorization", `Bearer ${token}`);
  }
  
  try {
    return await next(req);
  } catch (error: any) {
    // Check if it's a 401 Unauthenticated error
    if (error?.code === "unauthenticated") {
      localStorage.removeItem("taxos_token");
      window.location.href = "/";
    }
    throw error;
  }
};

const createClient = () => {
  return createPromiseClient(
    TaxosApi,
    createConnectTransport({
      baseUrl,
      interceptors: [tokenInterceptor],
    })
  );
};

export const client = createClient();

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
