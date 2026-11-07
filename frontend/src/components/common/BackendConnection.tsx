"use client";
import { useSyncExternalStore } from "react";
import { connectionSnapshot, serverConnectionSnapshot, subscribeConnection } from "@/services/backendConnection";
import { LoadingScene } from "./LoadingScene";
export function BackendConnection() {
  const connecting = useSyncExternalStore(subscribeConnection, connectionSnapshot, serverConnectionSnapshot);
  if (!connecting) return null;
  return <div className="j-navigation-loader j-navigation-loader--welcome" style={{ zIndex: 150 }}>
    <LoadingScene variant="welcome" title="Connecting to JOMO…" description="Our service may be waking up. This can take about a minute. Your saved session is being kept." />
  </div>;
}
