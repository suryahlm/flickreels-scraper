import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone', // Required for Docker deployment
};

export default nextConfig;
// force build cache invalidation Thu Jun 25 01:24:35 WIB 2026
