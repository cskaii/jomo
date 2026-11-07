import { assessPassword } from "./passwordStrength";

// This worker receives data only from the local form and never makes API calls.
self.addEventListener("message", (event: MessageEvent<{
  id: number; password: string; email: string;
}>) => {
  const { id, password, email } = event.data;
  self.postMessage({ id, result: assessPassword(password, email) });
});
