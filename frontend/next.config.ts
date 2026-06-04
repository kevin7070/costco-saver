import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Django expects trailing slashes; don't let Next.js redirect
  skipTrailingSlashRedirect: true,
};

export default nextConfig;
