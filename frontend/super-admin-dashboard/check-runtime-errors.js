#!/usr/bin/env node

const puppeteer = require('puppeteer');
const chalk = require('chalk').default || require('chalk');

/**
 * 브라우저에서 Next.js 앱의 런타임 에러를 자동으로 체크하는 스크립트
 */
async function checkRuntimeErrors() {
  const baseUrl = 'http://localhost:3020';
  const pages = [
    '/',
    '/admins',
    '/analytics', 
    '/audit-compliance',
    '/energy',
    '/energy/auto-purchase',
    '/energy/external-market',
    '/energy/purchase-history',
    '/energy-market',
    '/fees',
    '/integrated-dashboard',
    '/partner-onboarding',
    '/partners',
    '/partner-energy',
    '/settings'
  ];

  console.log(chalk.blue('🔍 런타임 에러 체크를 시작합니다...'));
  console.log(chalk.gray(`Base URL: ${baseUrl}`));

  let browser;
  try {
    browser = await puppeteer.launch({ 
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    // 콘솔 에러 수집
    const errors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push({
          text: msg.text(),
          location: msg.location(),
          timestamp: new Date().toISOString()
        });
      }
    });

    // 페이지 에러 수집
    page.on('pageerror', (error) => {
      errors.push({
        text: error.message,
        stack: error.stack,
        type: 'pageerror',
        timestamp: new Date().toISOString()
      });
    });

    // 각 페이지 체크
    for (const pagePath of pages) {
      const url = `${baseUrl}${pagePath}`;
      
      try {
        console.log(chalk.gray(`📄 체크 중: ${url}`));
        
        // 페이지 로드
        await page.goto(url, { 
          waitUntil: 'networkidle0',
          timeout: 10000 
        });
        
        // React 컴포넌트가 렌더링될 시간을 줌
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // 에러가 있으면 출력
        if (errors.length > 0) {
          console.log(chalk.red(`❌ ${url}에서 에러 발견:`));
          errors.forEach((error, index) => {
            console.log(chalk.red(`  ${index + 1}. ${error.text}`));
            if (error.location) {
              console.log(chalk.gray(`     위치: ${error.location.url}:${error.location.lineNumber}`));
            }
          });
          errors.length = 0; // 에러 배열 초기화
        } else {
          console.log(chalk.green(`✅ ${url} - 에러 없음`));
        }
        
      } catch (err) {
        console.log(chalk.red(`❌ ${url} 로드 실패: ${err.message}`));
      }
    }

  } catch (err) {
    console.error(chalk.red('브라우저 실행 실패:', err.message));
    process.exit(1);
  } finally {
    if (browser) {
      await browser.close();
    }
  }

  console.log(chalk.blue('🎉 런타임 에러 체크 완료!'));
}

// 서버가 실행 중인지 확인
async function checkServerStatus() {
  try {
    const http = require('http');
    return new Promise((resolve) => {
      const req = http.get('http://localhost:3020', (res) => {
        resolve(res.statusCode === 200);
      });
      req.on('error', () => {
        resolve(false);
      });
      req.setTimeout(5000, () => {
        req.destroy();
        resolve(false);
      });
    });
  } catch {
    return false;
  }
}

// 메인 실행
async function main() {
  console.log(chalk.blue('🚀 Next.js 런타임 에러 체커'));
  console.log(chalk.gray('=' .repeat(50)));

  // 서버 상태 확인 (건너뛰기 - 직접 페이지 로드로 확인)
  console.log(chalk.gray('서버 상태 확인을 건너뛰고 직접 페이지 로드를 시도합니다...\n'));

  await checkRuntimeErrors();
}

// 실행
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { checkRuntimeErrors };
