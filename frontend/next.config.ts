import type { NextConfig } from "next";

const DJANGO_API_URL = process.env.DJANGO_API_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  // Django expects trailing slashes; don't let Next.js redirect
  skipTrailingSlashRedirect: true,
  async rewrites() {
    // Receipt images live in Django's MEDIA; proxy /media/* to the backend
    // so same-origin <img src="/media/..."> works.
    return [
      { source: "/media/:path*", destination: `${DJANGO_API_URL}/media/:path*` },
    ];
  },
};

export default nextConfig;
