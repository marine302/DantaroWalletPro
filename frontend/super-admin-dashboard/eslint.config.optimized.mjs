/**
 * ESLint 설정 업데이트
 * - any 타입 사용을 제한적으로 허용
 * - 사용하지 않는 변수들에 대한 경고 완화
 * - 개발 환경에서 필요한 규칙들 조정
 */

const { defineConfig } = require('eslint-define-config');

module.exports = defineConfig({
  extends: ['next/core-web-vitals'],
  rules: {
    // TypeScript 관련 규칙 완화
    '@typescript-eslint/no-explicit-any': 'warn', // 에러에서 경고로 변경
    '@typescript-eslint/no-unused-vars': [
      'warn',
      {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
        caughtErrorsIgnorePattern: '^_'
      }
    ],
    
    // React 관련 규칙
    'react-hooks/exhaustive-deps': 'warn',
    'react/no-unescaped-entities': 'warn',
    
    // 개발 중 허용할 규칙들
    'prefer-const': 'warn',
    'no-console': 'warn', // 개발 중에는 console.log 허용
    
    // 임시로 비활성화할 규칙들 (점진적 개선)
    '@typescript-eslint/ban-ts-comment': 'warn',
    '@typescript-eslint/no-non-null-assertion': 'warn'
  },
  overrides: [
    {
      files: ['**/*.ts', '**/*.tsx'],
      rules: {
        // TypeScript 파일에서만 적용할 규칙들
        '@typescript-eslint/no-inferrable-types': 'off'
      }
    },
    {
      files: ['**/mock-*.js', '**/test-*.js', '**/*.test.ts', '**/*.test.tsx'],
      rules: {
        // Mock 파일과 테스트 파일에서는 더 관대하게
        '@typescript-eslint/no-explicit-any': 'off',
        'no-console': 'off'
      }
    }
  ]
});
