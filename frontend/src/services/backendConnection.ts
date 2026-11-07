const api = process.env.NEXT_PUBLIC_API_BASE_URL || "/api/v1";
let pending: Promise<void> | null = null;
let connecting = false;
const listeners = new Set<() => void>();
export const connectionSnapshot = () => connecting;
export const serverConnectionSnapshot = () => false;
export function subscribeConnection(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}
function update(value: boolean) { connecting = value; listeners.forEach(listener => listener()); }
// Probe only a public, read-only endpoint. Never replay a mutation after a timeout.
export function waitForBackend(): Promise<void> {
  if (pending) return pending;
  update(true);
  pending = (async () => {
    const deadline = Date.now() + 90000;
    while (Date.now() < deadline) {
      try {
        const response = await fetch(`${api}/privacy-notice`, { cache: "no-store", signal: AbortSignal.timeout(Math.min(10000, deadline - Date.now())) });
        if (response.ok && response.headers.get("content-type")?.includes("application/json")) return;
      } catch { /* Cold start or offline: bounded retry, no credentials in probes. */ }
      if (Date.now() < deadline) await new Promise(resolve => setTimeout(resolve, 2000));
    }
    throw new Error("JOMO is taking longer to connect. Your saved session has been kept. Please retry shortly.");
  })().finally(() => { pending = null; update(false); });
  return pending;
}
