import { Suspense, type ReactNode } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageLoading } from "@/components/common/PageLoading";
export default function MainLayout({ children }: { children: ReactNode }) {
  return (
    <Suspense fallback={<PageLoading fullScreen />}>
      <AppShell>{children}</AppShell>
    </Suspense>
  );
}
