#!/usr/bin/env node
/* eslint-disable @typescript-eslint/no-require-imports */
/* eslint-disable @typescript-eslint/no-unused-vars */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

/**
 * 향상된 자동화 시스템
 */
class EnhancedAutoFixer {
  constructor() {
    this.logsDir = path.join(process.cwd(), 'logs');
    this.srcDir = path.join(process.cwd(), 'src');
    this.maxRetries = 3;
    this.retryCount = 0;
    this.fixHistory = [];
    this.knownIssues = new Map();
    this.initializeKnownIssues();
  }

  /**
   * 알려진 이슈 패턴 초기화
   */
  initializeKnownIssues() {
    this.knownIssues.set('INVALID_ELEMENT_TYPE', {
      pattern: /Element type is invalid/,
      commonCauses: [
        'export default 누락',
        'import 구문 오류',
        '컴포넌트 이름 불일치',
        '순환 참조'
      ],
      fixes: [
        'checkExportDefault',
        'checkImportSyntax',
        'checkComponentName',
        'checkCircularDependency'
      ]
    });

    this.knownIssues.set('MODULE_NOT_FOUND', {
      pattern: /Module not found/,
      commonCauses: [
        '잘못된 경로',
        '누락된 파일',
        '패키지 미설치'
      ],
      fixes: [
        'checkFilePath',
        'checkPackageInstall',
        'checkImportPath'
      ]
    });

    this.knownIssues.set('TYPESCRIPT_ERROR', {
      pattern: /Property .* does not exist/,
      commonCauses: [
        '타입 정의 오류',
        '인터페이스 불일치',
        '선택적 속성 누락'
      ],
      fixes: [
        'checkTypeDefinition',
        'checkInterface',
        'addOptionalProperty'
      ]
    });
  }

  /**
   * 로그 파일에서 최신 오류 읽기
   */
  readLatestErrors() {
    try {
      if (!fs.existsSync(this.logsDir)) {
        return [];
      }

      const files = fs.readdirSync(this.logsDir)
        .filter(file => file.startsWith('frontend-errors-'))
        .sort()
        .reverse();

      if (files.length === 0) {
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
   * 고급 오류 분석
   */
  analyzeErrorAdvanced(error) {
    const message = error.message || '';
    const stack = error.stack || '';
    const componentStack = error.componentStack || '';
    
    // 알려진 이슈 패턴 매칭
    for (const [type, issue] of this.knownIssues) {
      if (issue.pattern.test(message)) {
        return {
          type,
          severity: this.calculateSeverity(error),
          description: `${type}: ${issue.commonCauses.join(', ')}`,
          suggestedFixes: issue.fixes,
          confidence: this.calculateConfidence(error, issue),
          affectedFiles: this.extractAffectedFiles(error),
          context: {
            message,
            stack,
            componentStack
          }
        };
      }
    }

    return {
      type: 'UNKNOWN',
      severity: 'LOW',
      description: '알 수 없는 오류',
      suggestedFixes: ['manual'],
      confidence: 0.1,
      affectedFiles: [],
      context: { message, stack, componentStack }
    };
  }

  /**
   * 오류 심각도 계산
   */
  calculateSeverity(error) {
    const message = error.message || '';
    
    if (message.includes('Element type is invalid') || 
        message.includes('Module not found')) {
      return 'HIGH';
    }
    
    if (message.includes('Property') && message.includes('does not exist')) {
      return 'MEDIUM';
    }
    
    return 'LOW';
  }

  /**
   * 수정 신뢰도 계산
   */
  calculateConfidence(error, issue) {
    let confidence = 0.5;
    
    // 스택 트레이스가 있으면 신뢰도 증가
    if (error.stack) confidence += 0.2;
    
    // 컴포넌트 스택이 있으면 신뢰도 증가
    if (error.componentStack) confidence += 0.2;
    
    // 파일 경로가 명확하면 신뢰도 증가
    if (this.extractAffectedFiles(error).length > 0) confidence += 0.1;
    
    return Math.min(confidence, 1.0);
  }

  /**
   * 영향받은 파일 추출
   */
  extractAffectedFiles(error) {
    const files = [];
    const text = `${error.message} ${error.stack} ${error.componentStack}`;
    
    // 파일 경로 패턴 매칭
    const fileMatches = text.match(/(?:at|in)\s+([^(\s]+\.(tsx?|jsx?|js|ts))/g);
    if (fileMatches) {
      fileMatches.forEach(match => {
        const filePath = match.replace(/^(?:at|in)\s+/, '');
        if (filePath.includes('src/')) {
          files.push(filePath);
        }
      });
    }
    
    return [...new Set(files)];
  }

  /**
   * export default 확인 및 수정
   */
  checkExportDefault(analysis) {
    const files = analysis.affectedFiles.length > 0 ? 
      analysis.affectedFiles : 
      [path.join(this.srcDir, 'components', 'wallet', 'WalletConnection.tsx')];
    
    let fixed = false;
    
    for (const filePath of files) {
      const fullPath = filePath.startsWith('/') ? filePath : path.join(process.cwd(), filePath);
      
      if (fs.existsSync(fullPath)) {
        let content = fs.readFileSync(fullPath, 'utf-8');
        
        // function 또는 const 컴포넌트 찾기
        const functionMatch = content.match(/(?:function|const)\s+(\w+)/);
        if (functionMatch) {
          const componentName = functionMatch[1];
          
          // export default 없는 경우 추가
          if (!content.includes('export default')) {
            content += `\nexport default ${componentName};\n`;
            fs.writeFileSync(fullPath, content);
            console.log(`✅ ${filePath}에 export default 추가됨`);
            fixed = true;
          }
        }
      }
    }
    
    return fixed;
  }

  /**
   * import 구문 확인 및 수정
   */
  checkImportSyntax(analysis) {
    const message = analysis.context.message;
    
    // WalletConnection 관련 오류인지 확인
    if (message.includes('WalletConnection')) {
      const pageFile = path.join(this.srcDir, 'app', 'page.tsx');
      
      if (fs.existsSync(pageFile)) {
        let content = fs.readFileSync(pageFile, 'utf-8');
        
        // 잘못된 import 구문 수정
        if (content.includes('import { WalletConnection }')) {
          content = content.replace(
            'import { WalletConnection }',
            'import WalletConnection'
          );
          fs.writeFileSync(pageFile, content);
          console.log('✅ WalletConnection import 구문 수정됨');
          return true;
        }
      }
    }
    
    return false;
  }

  /**
   * 컴포넌트 이름 확인
   */
  checkComponentName(analysis) {
    // 컴포넌트 이름 불일치 확인 및 수정
    return false;
  }

  /**
   * 순환 참조 확인
   */
  checkCircularDependency(analysis) {
    // 순환 참조 탐지 및 수정
    return false;
  }

  /**
   * 수정 실행
   */
  async executeFix(analysis) {
    const fixes = analysis.suggestedFixes;
    let fixedCount = 0;
    
    for (const fixMethod of fixes) {
      try {
        let fixed = false;
        
        switch (fixMethod) {
          case 'checkExportDefault':
            fixed = this.checkExportDefault(analysis);
            break;
          case 'checkImportSyntax':
            fixed = this.checkImportSyntax(analysis);
            break;
          case 'checkComponentName':
            fixed = this.checkComponentName(analysis);
            break;
          case 'checkCircularDependency':
            fixed = this.checkCircularDependency(analysis);
            break;
          default:
            console.log(`⚠️  알 수 없는 수정 방법: ${fixMethod}`);
            break;
        }
        
        if (fixed) {
          fixedCount++;
          this.fixHistory.push({
            timestamp: new Date().toISOString(),
            errorType: analysis.type,
            fixMethod,
            success: true
          });
        }
      } catch (error) {
        console.error(`❌ 수정 실패 (${fixMethod}):`, error);
        this.fixHistory.push({
          timestamp: new Date().toISOString(),
          errorType: analysis.type,
          fixMethod,
          success: false,
          error: error.message
        });
      }
    }
    
    return fixedCount;
  }

  /**
   * 메인 자동 수정 프로세스
   */
  async autoFixAdvanced() {
    console.log('🚀 고급 자동 수정 프로세스 시작...');
    
    if (this.retryCount >= this.maxRetries) {
      console.log('❌ 최대 재시도 횟수 초과');
      return false;
    }

    const errors = this.readLatestErrors();
    if (errors.length === 0) {
      console.log('✅ 감지된 오류가 없습니다.');
      return true;
    }

    console.log(`📋 ${errors.length}개의 오류 감지됨`);

    let totalFixed = 0;
    for (const error of errors) {
      const analysis = this.analyzeErrorAdvanced(error);
      console.log(`🔍 고급 분석: ${analysis.type} (신뢰도: ${(analysis.confidence * 100).toFixed(1)}%)`);
      console.log(`📄 영향받은 파일: ${analysis.affectedFiles.join(', ') || '없음'}`);
      
      if (analysis.confidence > 0.5) {
        const fixed = await this.executeFix(analysis);
        totalFixed += fixed;
        
        if (fixed > 0) {
          console.log(`✅ ${fixed}개 수정 완료: ${analysis.description}`);
        }
      } else {
        console.log(`⚠️  신뢰도 낮음, 수동 확인 필요: ${analysis.description}`);
      }
    }

    console.log(`📊 총 ${totalFixed}개 수정됨`);

    // 수정 후 검증
    if (totalFixed > 0) {
      return this.validateFixes();
    }

    return totalFixed > 0;
  }

  /**
   * 수정 검증
   */
  validateFixes() {
    console.log('🧪 수정 검증 중...');
    
    try {
      // 타입 체크
      execSync('npm run build', { 
        cwd: process.cwd(),
        stdio: 'pipe' 
      });
      
      console.log('✅ 빌드 성공');
      return true;
    } catch (buildError) {
      console.log('❌ 빌드 실패, 추가 수정 필요');
      this.retryCount++;
      
      if (this.retryCount < this.maxRetries) {
        console.log(`🔄 재시도 (${this.retryCount}/${this.maxRetries})`);
        return this.autoFixAdvanced();
      }
      
      return false;
    }
  }

  /**
   * 수정 히스토리 출력
   */
  printFixHistory() {
    console.log('\n📈 수정 히스토리:');
    this.fixHistory.forEach((fix, index) => {
      const status = fix.success ? '✅' : '❌';
      console.log(`${index + 1}. ${status} ${fix.timestamp} - ${fix.errorType}: ${fix.fixMethod}`);
    });
  }

  /**
   * 실시간 모니터링
   */
  startAdvancedMonitoring() {
    console.log('🔍 고급 실시간 모니터링 시작...');
    
    setInterval(async () => {
      try {
        const result = await this.autoFixAdvanced();
        if (result) {
          this.printFixHistory();
        }
      } catch (error) {
        console.error('모니터링 중 오류:', error);
      }
    }, 15000); // 15초마다 체크
  }
}

// 스크립트 실행
if (require.main === module) {
  const autoFixer = new EnhancedAutoFixer();
  
  const args = process.argv.slice(2);
  const command = args[0];

  switch (command) {
    case 'fix':
      autoFixer.autoFixAdvanced();
      break;
    case 'monitor':
      autoFixer.startAdvancedMonitoring();
      break;
    case 'history':
      autoFixer.printFixHistory();
      break;
    default:
      console.log('🔧 향상된 자동 수정 시스템');
      console.log('사용법:');
      console.log('  node enhanced-auto-fix.js fix      - 고급 자동 수정 실행');
      console.log('  node enhanced-auto-fix.js monitor  - 고급 실시간 모니터링');
      console.log('  node enhanced-auto-fix.js history  - 수정 히스토리 출력');
      break;
  }
}

module.exports = EnhancedAutoFixer;
