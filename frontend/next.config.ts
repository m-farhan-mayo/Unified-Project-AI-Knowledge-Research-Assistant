import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // AI generation, SDK retries, and PDF indexing can exceed the 30s default.
  experimental: { proxyTimeout: 300_000 },
  async rewrites() {
    const backendUrl = (process.env.BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
    return [{ source: "/api/:path*", destination: `${backendUrl}/api/:path*` }];
  },
};

export default nextConfig;
