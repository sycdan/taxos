import React, { useState } from "react";
import { LogIn } from "lucide-react";
import { setToken } from "../api/client";
import { createPromiseClient } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";
import { TaxosApi } from "../api/v1/taxos_service_connect";
import { AuthenticateRequest } from "../api/v1/taxos_service_pb";

interface LoginModalProps {
  isOpen: boolean;
  onLogin: (token: string) => void;
}

const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onLogin }) => {
  const [token, setTokenInput] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const validateToken = async (tokenToValidate: string): Promise<boolean> => {
    try {
      const baseUrl = import.meta.env.VITE_GRPC_API_URL || "http://localhost:8080";
      
      // Create a temporary client with the test token
      const testClient = createPromiseClient(
        TaxosApi,
        createConnectTransport({
          baseUrl,
          interceptors: [
            (next: any) => async (req: any) => {
              req.header.set("Authorization", `Bearer ${tokenToValidate}`);
              return await next(req);
            },
          ],
        })
      );

      // Use the authenticate endpoint to validate the token
      await testClient.authenticate(new AuthenticateRequest({ token: tokenToValidate }));
      return true;
    } catch (err: any) {
      // If it's a 401 or unauthenticated error, token is invalid
      if (err?.code === "unauthenticated" || err?.status === 401) {
        return false;
      }
      // Other errors might be due to network issues, so be lenient
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) {
      setError("Please enter an access token");
      return;
    }

    setLoading(true);
    setError("");

    try {
      // Validate the token first
      const isValid = await validateToken(token);
      if (!isValid) {
        setError("Invalid access token. Please check and try again.");
        setLoading(false);
        return;
      }

      // Token is valid, store it and proceed
      setToken(token);
      onLogin(token);
    } catch (err) {
      setError("Failed to validate token. Please try again.");
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
        <div className="flex items-center justify-center mb-6">
          <LogIn className="w-8 h-8 text-blue-600 mr-2" />
          <h2 className="text-2xl font-bold text-gray-900">Access Required</h2>
        </div>

        <p className="text-gray-600 mb-6">
          Please enter your access token to continue.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="token"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Access Token
            </label>
            <input
              id="token"
              type="password"
              value={token}
              onChange={(e) => setTokenInput(e.target.value)}
              placeholder="Paste your access token"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition"
          >
            {loading ? "Validating..." : "Continue"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginModal;
