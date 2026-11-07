import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { BackendConnection } from "@/components/common/BackendConnection";
export const metadata: Metadata = {
  title: "JOMO — Less scrolling. More living.",
  description: "Make space for meaningful offline moments, together.",
};
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}<BackendConnection /></body>
    </html>
  );
}
