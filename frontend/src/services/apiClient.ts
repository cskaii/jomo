import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { ErrorEnvelope } from "@/types/api";
import { accessToken, clearSession } from "./authSession";
import { waitForBackend } from "./backendConnection";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "/api/v1";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

apiClient.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    if (["/auth/login", "/auth/register", "/auth/recover"].includes(config.url || "")) await waitForBackend();
    if (["/auth/login", "/auth/register", "/auth/recover", "/auth/refresh", "/auth/dev-session"].includes(config.url || "") || config.headers.Authorization) return config;
    const token = await accessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ErrorEnvelope>) => {
    const config = error.config as (InternalAxiosRequestConfig & { _jomoRetried?: boolean; _connectionRetried?: boolean }) | undefined;
    const temporary = !error.response || [502, 503, 504].includes(error.response.status);
    if (temporary && config && !config._connectionRetried && config.method === "get") {
      config._connectionRetried = true;
      try { await waitForBackend(); return apiClient.request(config); }
      catch (failure) { return Promise.reject(failure); }
    }
    if (error.response?.status === 401 && config && !config._jomoRetried && !config.url?.startsWith("/auth/")) {
      config._jomoRetried = true;
      try {
        const token = await accessToken(true);
        if (token) { config.headers.Authorization = `Bearer ${token}`; return apiClient.request(config); }
      } catch (failure) { return Promise.reject(failure); }
    }
    if (error.response?.status === 401 && !config?.url?.startsWith("/auth/") && typeof window !== "undefined") {
      clearSession();
      window.dispatchEvent(new Event("jomo:session-expired"));
    }
    if (error.response?.data?.error) {
      // Backend structured error envelope
      return Promise.reject({
        ...error.response.data.error,
        status: error.response.status,
        request_id: error.response.data.request_id,
      });
    }
    const status = error.response?.status;
    const mutation = !!config?.method && !["get", "head", "options"].includes(config.method.toLowerCase());
    const timedOut = ["ECONNABORTED", "ETIMEDOUT"].includes(error.code ?? "") || status === 504;
    const unavailable = !status || [502, 503, 504].includes(status);
    return Promise.reject({
      code: timedOut ? "REQUEST_TIMEOUT" : status ? "HTTP_ERROR" : "NETWORK_ERROR",
      message: unavailable && mutation
        ? "The server did not confirm this action. It may have completed. Refresh the status before trying again."
        : timedOut
        ? "The backend did not respond in time. Please retry shortly."
        : unavailable
        ? "JOMO cannot reach its backend. Please retry shortly or contact the team."
        : `The backend request failed (HTTP ${status}). Please retry.`,
      status,
      details: null,
    });
  },
);
