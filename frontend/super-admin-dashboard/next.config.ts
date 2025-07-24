import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Basic image optimization
  images: {
    domains: ['images.unsplash.com'],
  },

  // Basic security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
        ],
      },
    ];
  },

  // Fast refresh for development
  experimental: {
    serverComponentsExternalPackages: ['@tanstack/react-query'],
  },

  // Basic compiler optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // Enable SWC minification
  swcMinify: true,
};

export default nextConfig;
