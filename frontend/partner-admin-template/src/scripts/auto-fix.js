#!/usr/bin/env node
/* eslint-disable @typescript-eslint/no-require-imports */
/* eslint-disable @typescript-eslint/no-unused-vars */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

/**
 * 자동화된 오류 감지 및 수정 스크립트
 */
class AutoFixer {
  constructor() {
    this.logsDir = path.join(process.cwd(), 'logs');
    this.srcDir = path.join(process.cwd(), 'src');
    this.maxRetries = 3;
    this.retryCount = 0;
  }

  /**
   * 로그 파일에서 최신 오류 읽기
   */
  readLatestErrors() {
    try {
      if (!fs.existsSync(this.logsDir)) {
        console.log('로그 디렉터리가 없습니다.');
        return [];
      }

      const files = fs.readdirSync(this.logsDir)
        .filter(file => file.startsWith('frontend-errors-'))
        .sort()
        .reverse();

      if (files.length === 0) {
        console.log('오류 로그 파일이 없습니다.');
        return [];
      }

      const latestFile = files[0];
      const logPath = path.join(this.logsDir, latestFile);
      const content = fs.readFileSync(logPath, 'utf-8');
      
      const errors = content.split('\n')
        .filter(line => line.trim())
        .map(line => {
          try {
            return JSON.parse(line);
          } catch (e) {
            return null;
          }
        })
        .filter(error => error !== null);

      return errors;
    } catch (error) {
      console.error('오류 로그 읽기 실패:', error);
      return [];
    }
  }

  /**
   * 오류 유형 분석
   */
  analyzeError(error) {
    const message = error.message || '';
    const stack = error.stack || '';
    
    // 컴포넌트 import/export 오류
    if (message.includes('Element type is invalid')) {
      return {
        type: 'INVALID_ELEMENT_TYPE',
        severity: 'HIGH',
        description: 'React 컴포넌트 import/export 오류',
        suggestedFix: 'checkImportExport'
      };
    }

    // 모듈 not found 오류
    if (message.includes('Module not found')) {
      return {
        type: 'MODULE_NOT_FOUND',
        severity: 'HIGH',
        description: '모듈을 찾을 수 없음',
        suggestedFix: 'checkModulePath'
      };
    }

    // 함수 not defined 오류
    if (message.includes('is not defined')) {
      return {
        type: 'UNDEFINED_VARIABLE',
        severity: 'MEDIUM',
        description: '정의되지 않은 변수/함수',
        suggestedFix: 'checkVariableDefinition'
      };
    }

    // 타입스크립트 오류
    if (message.includes('Property') && message.includes('does not exist')) {
      return {
        type: 'TYPESCRIPT_ERROR',
        severity: 'MEDIUM',
        description: 'TypeScript 타입 오류',
        suggestedFix: 'checkTypeDefinition'
      };
    }

    return {
      type: 'UNKNOWN',
      severity: 'LOW',
      description: '알 수 없는 오류',
      suggestedFix: 'manual'
    };
  }

  /**
   * Import/Export 오류 수정
   */
  fixImportExport(error) {
    console.log('Import/Export 오류 수정 중...');
    
    // WalletConnection 컴포넌트 관련 오류일 가능성이 높음
    const walletConnectionPath = path.join(this.srcDir, 'components', 'wallet', 'WalletConnection.tsx');
    const pageFilePath = path.join(this.srcDir, 'app', 'page.tsx');
    
    try {
      // WalletConnection 파일 확인
      if (fs.existsSync(walletConnectionPath)) {
        let content = fs.readFileSync(walletConnectionPath, 'utf-8');
        
        // export default 확인 및 수정
        if (!content.includes('export default')) {
          // 마지막 export 찾기
          const lines = content.split('\n');
          const lastExportIndex = lines.findIndex(line => line.includes('export'));
          
          if (lastExportIndex !== -1) {
            lines[lastExportIndex] = lines[lastExportIndex].replace('export', 'export default');
            content = lines.join('\n');
            fs.writeFileSync(walletConnectionPath, content);
            console.log('WalletConnection export 수정됨');
          }
        }
      }

      // page.tsx 파일 확인
      if (fs.existsSync(pageFilePath)) {
        let content = fs.readFileSync(pageFilePath, 'utf-8');
        
        // import 방식 확인 및 수정
        if (content.includes('import { WalletConnection }')) {
          content = content.replace(
            'import { WalletConnection }',
            'import WalletConnection'
          );
          fs.writeFileSync(pageFilePath, content);
          console.log('page.tsx import 수정됨');
        }
      }

      return true;
    } catch (error) {
      console.error('Import/Export 수정 실패:', error);
      return false;
    }
  }

  /**
   * 모듈 경로 오류 수정
   */
  fixModulePath(error) {
    console.log('모듈 경로 오류 수정 중...');
    // 구현 필요
    return false;
  }

  /**
   * 자동 수정 실행
   */
  async autoFix() {
    console.log('🔧 자동 수정 프로세스 시작...');
    
    if (this.retryCount >= this.maxRetries) {
      console.log('❌ 최대 재시도 횟수 초과');
      return false;
    }

    // 1. 최신 오류 읽기
    const errors = this.readLatestErrors();
    if (errors.length === 0) {
      console.log('✅ 감지된 오류가 없습니다.');
      return true;
    }

    console.log(`📋 ${errors.length}개의 오류 감지됨`);

    // 2. 오류 분석 및 수정
    let fixedCount = 0;
    for (const error of errors) {
      const analysis = this.analyzeError(error);
      console.log(`🔍 오류 분석: ${analysis.type} - ${analysis.description}`);
      
      let fixed = false;
      switch (analysis.suggestedFix) {
        case 'checkImportExport':
          fixed = this.fixImportExport(error);
          break;
        case 'checkModulePath':
          fixed = this.fixModulePath(error);
          break;
        default:
          console.log(`⚠️  수동 수정 필요: ${analysis.description}`);
          break;
      }

      if (fixed) {
        fixedCount++;
        console.log(`✅ 오류 수정됨: ${analysis.description}`);
      }
    }

    console.log(`📊 ${fixedCount}/${errors.length}개 오류 수정됨`);

    // 3. 수정 후 테스트
    if (fixedCount > 0) {
      console.log('🧪 수정된 코드 테스트 중...');
      
      try {
        // Next.js 빌드 테스트
        execSync('npm run build', { 
          cwd: process.cwd(),
          stdio: 'pipe' 
        });
        console.log('✅ 빌드 성공');
        return true;
      } catch (buildError) {
        console.log('❌ 빌드 실패, 재시도 중...');
        this.retryCount++;
        
        // 잠시 대기 후 재시도
        await new Promise(resolve => setTimeout(resolve, 2000));
        return this.autoFix();
      }
    }

    return fixedCount > 0;
  }

  /**
   * 실시간 모니터링 시작
   */
  startMonitoring() {
    console.log('👁️  실시간 오류 모니터링 시작...');
    
    setInterval(async () => {
      const result = await this.autoFix();
      if (result) {
        console.log('🔄 자동 수정 완료, 모니터링 계속...');
      }
    }, 10000); // 10초마다 체크
  }
}

// 스크립트 실행
if (require.main === module) {
  const autoFixer = new AutoFixer();
  
  const args = process.argv.slice(2);
  const command = args[0];

  switch (command) {
    case 'fix':
      autoFixer.autoFix();
      break;
    case 'monitor':
      autoFixer.startMonitoring();
      break;
    default:
      console.log('사용법:');
      console.log('  node auto-fix.js fix      - 한 번 자동 수정 실행');
      console.log('  node auto-fix.js monitor  - 실시간 모니터링 시작');
      break;
  }
}

module.exports = AutoFixer;
