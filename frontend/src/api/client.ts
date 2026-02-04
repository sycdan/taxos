import { createPromiseClient } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";
import { TaxosApi } from "./v1/taxos_service_connect";

const baseUrl = import.meta.env.VITE_GRPC_API_URL || "http://localhost:8080";

export const client = createPromiseClient(
  TaxosApi,
  createConnectTransport({ baseUrl })
);
