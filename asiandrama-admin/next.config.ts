import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone', // Required for Docker deployment
  compress: true,
  poweredByHeader: false,
};

export default nextConfig;
