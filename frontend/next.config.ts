import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  // Keep deployment on stable features; the prototype does not require caching.
  async rewrites() {
    const backend = (process.env.BACKEND_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
    return [{ source: "/api/v1/:path*", destination: `${backend}/api/v1/:path*` }];
  },
  outputFileTracingRoot: path.join(__dirname, ".."),
  turbopack: {
    root: path.join(__dirname, ".."),
  },
};

export default nextConfig;
