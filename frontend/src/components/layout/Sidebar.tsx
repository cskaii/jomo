"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Users, Compass, Flower2, Sparkles } from "lucide-react";

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  const navItems = [
    {
      label: "Insights",
      href: "/insights",
      icon: BarChart3,
      description: "Digital habits & wellbeing",
    },
    {
      label: "Friends & Groups",
      href: "/friends",
      icon: Users,
      description: "Circles and group activities",
    },
    {
      label: "Activities",
      href: "/activities",
      icon: Compass,
      description: "Discover & start offline missions",
    },
    {
      label: "Virtual Garden",
      href: "/garden",
      icon: Flower2,
      description: "Personal & shared sanctuaries",
    },
  ];

  return (
    <aside className="hidden sm:flex flex-col w-64 border-r border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/20 p-4 shrink-0">
      <div className="space-y-1">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-start gap-3 px-3.5 py-3 rounded-2xl transition-all ${
                isActive
                  ? "bg-emerald-600 text-white shadow-sm font-medium"
                  : "text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200/60 dark:hover:bg-zinc-800/60 hover:text-zinc-900 dark:hover:text-zinc-100"
              }`}
            >
              <Icon className="w-5 h-5 shrink-0 mt-0.5" />
              <div className="flex flex-col">
                <span className="text-sm leading-tight">{item.label}</span>
                <span
                  className={`text-[11px] mt-0.5 line-clamp-1 ${
                    isActive
                      ? "text-emerald-100"
                      : "text-zinc-400 dark:text-zinc-500"
                  }`}
                >
                  {item.description}
                </span>
              </div>
            </Link>
          );
        })}
      </div>

      <div className="mt-auto pt-6 border-t border-zinc-200 dark:border-zinc-800">
        <div className="p-3.5 rounded-2xl bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-950/30 dark:to-teal-950/20 border border-emerald-200/60 dark:border-emerald-800/40">
          <div className="flex items-center gap-2 text-emerald-800 dark:text-emerald-300 font-semibold text-xs mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Server-Verified Rewards</span>
          </div>
          <p className="text-[11px] text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Spend meaningful offline time with friends to grow your gardens.
          </p>
        </div>
      </div>
    </aside>
  );
};
