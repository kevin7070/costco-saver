import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Django expects trailing slashes; don't let Next.js redirect.
  skipTrailingSlashRedirect: true,
  // /media/* and /api/v1/* are proxied to Django via route handlers
  // (src/app/media + src/app/api) so the upstream host is resolved at runtime,
  // not baked at build time the way next.config rewrites would.
};

export default nextConfig;
