"use client";
import { usePathname } from "next/navigation";
import { LoadingScene } from "./LoadingScene";
import { loadingCopy } from "@/lib/loadingCopy";

export function PageLoading({ fullScreen = false }: { fullScreen?: boolean }) {
  const pathname = usePathname();
  return <LoadingScene {...loadingCopy(pathname ?? "")} variant={fullScreen ? "welcome" : "page"} />;
}
