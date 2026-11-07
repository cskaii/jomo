import React from "react";
import { LoadingScene } from "./LoadingScene";

interface LoadingProps {
  label?: string;
  size?: "sm" | "md" | "lg";
}

export const Loading: React.FC<LoadingProps> = ({
  label = "Your space is taking root.",
  size = "md",
}) => {
  return <LoadingScene title={label} variant={size === "lg" ? "page" : "inline"} />;
};
