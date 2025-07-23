import type { NextConfig } from "next";
import { securityHeaders } from "./src/lib/security";

const nextConfig: NextConfig = {
  /* Performance Optimizations */
  
  // Image optimization
  images: {
    domains: ['images.unsplash.com'],
    formats: ['image/webp', 'image/avif'],
  },

  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: securityHeaders,
      },
    ];
  },

  // Code splitting and chunking optimization
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    if (!dev && !isServer) {
      // Optimize chunk splitting
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          default: false,
          vendors: false,
          // Vendor libraries
          vendor: {
            name: 'vendor',
            chunks: 'all',
            test: /node_modules/,
            priority: 20,
          },
          // Common components
          common: {
            name: 'common',
            minChunks: 2,
            chunks: 'all',
            priority: 10,
            reuseExistingChunk: true,
            enforce: true,
          },
          // Large libraries
          recharts: {
            name: 'recharts',
            test: /[\\/]node_modules[\\/](recharts)[\\/]/,
            chunks: 'all',
            priority: 30,
          },
          tanstack: {
            name: 'tanstack',
            test: /[\\/]node_modules[\\/](@tanstack)[\\/]/,
            chunks: 'all',
            priority: 30,
          },
        },
      };
    }

    return config;
  },

  // Experimental features for better performance
  experimental: {
    optimizeCss: true,
    serverComponentsExternalPackages: ['@tanstack/react-query'],
  },

  // Compiler optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // Build optimization
  swcMinify: true,
  
  // Output optimization
  output: 'standalone',
};

export default nextConfig;
