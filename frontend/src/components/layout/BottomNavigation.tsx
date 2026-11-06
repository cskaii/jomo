"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Users, Compass, Flower2 } from "lucide-react";

export const BottomNavigation: React.FC = () => {
  const pathname = usePathname();

  const navItems = [
    { label: "Insights", href: "/insights", icon: BarChart3 },
    { label: "Friends", href: "/friends", icon: Users },
    { label: "Activities", href: "/activities", icon: Compass },
    { label: "Garden", href: "/garden", icon: Flower2 },
  ];

  return (
    <nav className="sm:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/90 dark:bg-zinc-950/90 backdrop-blur-md border-t border-zinc-200 dark:border-zinc-800 pb-safe">
      <div className="flex items-center justify-around h-16 px-2">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center justify-center flex-1 h-full gap-1 transition-colors ${
                isActive
                  ? "text-emerald-600 dark:text-emerald-400 font-semibold"
                  : "text-zinc-500 hover:text-zinc-800 dark:text-zinc-400 dark:hover:text-zinc-200"
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-[11px] leading-none">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
};
