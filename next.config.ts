import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/health",
        destination: "/api/health",
      },
      {
        source: "/:path((?!api/health).*)",
        destination: "http://localhost:8000/:path*",
      },
    ];
  },
};

export default nextConfig;
