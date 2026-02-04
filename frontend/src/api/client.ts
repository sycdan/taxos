import { createPromiseClient } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";
import { TaxosApi } from "./proto/v1/taxos_service_connect";

const baseUrl = import.meta.env.GRPC_API_URL;

export const client = createPromiseClient(
  TaxosApi,
  createConnectTransport({ baseUrl })
);
