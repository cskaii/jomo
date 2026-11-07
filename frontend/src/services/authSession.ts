import { z } from "zod";
import { clearResourceCache } from "@/lib/resourceCache";
import { waitForBackend } from "./backendConnection";

export const authSession = z.object({
  access_token: z.string().min(1), refresh_token: z.string().min(1),
  expires_in: z.number().positive(), token_type: z.string(),
});
const api = process.env.NEXT_PUBLIC_API_BASE_URL || "/api/v1";
let refreshing: Promise<string> | null = null;

export function clearSession() {
  clearResourceCache();
  for (const key of ["jomo_auth_token", "jomo_refresh_token", "jomo_token_expires_at"])
    localStorage.removeItem(key);
}

export function saveSession(value: z.infer<typeof authSession>) {
  const session = authSession.parse(value);
  if (sessionOwner(session.access_token) !== sessionOwner(localStorage.getItem("jomo_auth_token")))
    clearResourceCache();
  localStorage.setItem("jomo_auth_token", session.access_token);
  localStorage.setItem("jomo_refresh_token", session.refresh_token);
  localStorage.setItem("jomo_token_expires_at", String(Date.now() + session.expires_in * 1000));
}

export function sessionOwner(token: string | null): string {
  if (!token) return "";
  try {
    const payload = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const subject: unknown = JSON.parse(atob(payload)).sub;
    return typeof subject === "string" ? subject : token;
  } catch { return token; }
}

function expireSession() {
  clearSession();
  window.dispatchEvent(new Event("jomo:session-expired"));
}

export async function accessToken(forceRefresh = false): Promise<string | null> {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem("jomo_auth_token");
  if (!token) return null;
  if (process.env.NEXT_PUBLIC_DEV_AUTH_ENABLED === "true" && token.startsWith("dev-user-")) {
    if (Number(localStorage.getItem("jomo_token_expires_at")) > Date.now()) return token;
    expireSession();
    return null;
  }
  if (token.split(".").length !== 3) {
    expireSession();
    throw new Error("Sign in with your Supabase account. Development sessions are no longer supported.");
  }
  const expires = Number(localStorage.getItem("jomo_token_expires_at"));
  if (!forceRefresh && expires > Date.now() + 60000) return token;
  if (refreshing) return refreshing;
  refreshing = (async () => {
    const refresh = localStorage.getItem("jomo_refresh_token");
    if (!refresh) { expireSession(); throw new Error("Your session expired. Please sign in again."); }
    await waitForBackend();
    const response = await fetch(`${api}/auth/refresh`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }), cache: "no-store",
      signal: AbortSignal.timeout(20000),
    });
    if (!response.ok) {
      if ([400, 401, 403].includes(response.status)) expireSession();
      throw new Error(response.status >= 500 ? "Authentication is temporarily unavailable. Please retry." : "Your session expired. Please sign in again.");
    }
    const result = z.object({ data: authSession }).parse(await response.json());
    if (localStorage.getItem("jomo_auth_token") !== token || localStorage.getItem("jomo_refresh_token") !== refresh)
      throw new Error("The account session changed. Please retry.");
    saveSession(result.data);
    return result.data.access_token;
  })();
  try { return await refreshing; } finally { refreshing = null; }
}

export async function signOut() {
  try {
    const token = await accessToken();
    if (token) await fetch(`${api}/auth/logout`, {
      method: "POST", headers: { Authorization: `Bearer ${token}` }, cache: "no-store",
    });
  } finally { clearSession(); }
}
