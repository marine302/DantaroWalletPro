import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    rules: {
      // 자동 수정 가능한 규칙들 - unused 변수 경고로 변경
      "no-unused-vars": ["warn", { "argsIgnorePattern": "^_", "varsIgnorePattern": "^_" }],
      "@typescript-eslint/no-unused-vars": ["warn", { "argsIgnorePattern": "^_", "varsIgnorePattern": "^_" }],
      "prefer-const": "error",
      "no-var": "error",
      "object-shorthand": "error",
      "prefer-template": "error",
      // 경고로 설정하여 빌드를 막지 않도록
      "@typescript-eslint/no-explicit-any": "warn",
      "react-hooks/exhaustive-deps": "warn",
      "react/no-unescaped-entities": "warn",
      // Next.js 관련 규칙
      "@next/next/no-img-element": "warn",
      // 자동 수정을 위한 추가 규칙
      "no-extra-semi": "error",
      "no-multiple-empty-lines": ["error", { "max": 1 }],
      "eol-last": ["error", "always"],
      "no-trailing-spaces": "error",
      // require 허용
      "@typescript-eslint/no-require-imports": "warn",
      // display name 경고로 변경
      "react/display-name": "warn"
    }
  }
];

export default eslintConfig;
