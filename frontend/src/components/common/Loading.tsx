import React from "react";

interface LoadingProps {
  label?: string;
  size?: "sm" | "md" | "lg";
}

export const Loading: React.FC<LoadingProps> = ({
  label = "Loading...",
  size = "md",
}) => {
  const sizeMap = {
    sm: "w-4 h-4",
    md: "w-8 h-8",
    lg: "w-12 h-12",
  };

  return (
    <div className="flex flex-col items-center justify-center p-8 gap-3">
      <div
        className={`${sizeMap[size]} border-2 border-emerald-500 border-t-transparent rounded-full animate-spin`}
      />
      {label && <p className="text-sm text-zinc-500 dark:text-zinc-400">{label}</p>}
    </div>
  );
};
