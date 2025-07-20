/** @type {import('next').NextConfig} */
const nextConfig = {
    eslint: {
        // 프로덕션 빌드 시 ESLint 오류를 무시
        ignoreDuringBuilds: true,
    },
    typescript: {
        // 프로덕션 빌드 시 TypeScript 오류를 무시 (개발용)
        ignoreBuildErrors: true,
    },
}

module.exports = nextConfig
