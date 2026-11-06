"use client";

import React from "react";
import Link from "next/link";
import { ShieldCheck, User as UserIcon } from "lucide-react";

export const Header: React.FC = () => {
  return (
    <header className="sticky top-0 z-40 w-full bg-white/80 dark:bg-zinc-950/80 backdrop-blur-md border-b border-zinc-200 dark:border-zinc-800">
      <div className="flex h-16 items-center justify-between px-4 sm:px-8 max-w-7xl mx-auto">
        <Link href="/insights" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center text-white font-bold text-lg shadow-sm group-hover:scale-105 transition-transform">
            J
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-lg leading-tight tracking-tight text-zinc-900 dark:text-zinc-50">
              JOMO
            </span>
            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium tracking-wide uppercase">
              Joy of Missing Out
            </span>
          </div>
        </Link>

        <div className="flex items-center gap-3">
          <Link
            href="/privacy-guardian"
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 rounded-full hover:bg-emerald-100 transition-colors"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Privacy Guardian</span>
          </Link>

          <Link
            href="/settings"
            className="p-2 text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-xl transition-colors"
            title="Settings & Profile"
          >
            <UserIcon className="w-5 h-5" />
          </Link>
        </div>
      </div>
    </header>
  );
};
