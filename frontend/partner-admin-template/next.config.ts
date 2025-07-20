import type { NextConfig } from "next";

/**
 * DantaroWallet Partner Admin Template - Next.js 설정
 * 
 * 📋 포트 표준 (PORT_STANDARD.md 참조):
 * - Partner Admin: 3030 (이 프로젝트)
 * - Super Admin: 3020  
 * - Backend API: 8000
 * 
 * ⚠️ 포트 3030 고정 - 절대 변경 금지
 */

const nextConfig: NextConfig = {
  // 🔒 포트 고정 설정 - DantaroWallet 표준 준수
  experimental: {
    serverExternalPackages: [],
  },
  
  // 🛠️ 개발 서버 설정
  ...(process.env.NODE_ENV === 'development' && {
    compiler: {
      removeConsole: false, // 개발 중에는 콘솔 로그 유지
    },
  }),

  // 🌐 API 프록시 설정 (백엔드 포트 8000과 연동)
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}${process.env.NEXT_PUBLIC_API_VERSION}/:path*`,
      },
    ];
  },

  // 이미지 최적화 설정
  images: {
    domains: ['localhost'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },

  // 실험적 기능 설정
  experimental: {
    optimizePackageImports: ['lucide-react', '@radix-ui/react-icons'],
  },

  // TypeScript 설정
  typescript: {
    ignoreBuildErrors: false,
  },

  // ESLint 설정
  eslint: {
    ignoreDuringBuilds: false,
  },
};

export default nextConfig;
