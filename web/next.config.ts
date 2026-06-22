import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  // Pin the workspace root to this app (multiple lockfiles exist upstream).
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
