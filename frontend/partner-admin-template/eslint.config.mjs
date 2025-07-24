import { FlatCompat } from "@eslint/eslintrc";
import { dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    ignores: [
      "port-manager.js",  // Node.js 스크립트 제외
      "*.config.js",      // 설정 파일들 제외
      ".next/**",         // Next.js 빌드 파일 제외
    ]
  },
  {
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-unused-vars": "warn"
    }
  },
  {
    files: ["*.js"],
    rules: {
      "@typescript-eslint/no-require-imports": "off"  // JS 파일에서는 require 허용
    }
  }
];

export default eslintConfig;
