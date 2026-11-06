import { Suspense, type ReactNode } from "react";
import { AppShell } from "@/components/layout/AppShell";
export default function MainLayout({ children }: { children: ReactNode }) {
  return (
    <Suspense fallback={<p role="status">Opening your space…</p>}>
      <AppShell>{children}</AppShell>
    </Suspense>
  );
}
