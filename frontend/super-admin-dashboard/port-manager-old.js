#!/usr/bin/env node

/**
 * 포트 설정을 중앙에서 관리하는 스크립트
 * .env.local에서 NEXT_PUBLIC_FRONTEND_PORT를 읽어서 사용
 */

const fs = require('fs');
const path = require('path');

// .env.local 파일 읽기
const envPath = path.join(__dirname, '.env.local');
let frontendPort = 3020; // 기본값

if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf8');
  const match = envContent.match(/NEXT_PUBLIC_FRONTEND_PORT=(\d+)/);
  if (match) {
    frontendPort = parseInt(match[1]);
  }
}

// 명령어 인자에서 스크립트 타입 가져오기
const scriptType = process.argv[2];

if (!scriptType) {
  console.log('사용법: node port-manager.js [dev|start|build]');
  process.exit(1);
}

// Next.js 명령어 실행
const { spawn } = require('child_process');

let command;
let args;

switch (scriptType) {
  case 'dev':
    command = 'npx';
    args = ['next', 'dev', '--turbopack', '-p', frontendPort.toString()];
    break;
  case 'start':
    command = 'npx';
    args = ['next', 'start', '-p', frontendPort.toString()];
    break;
  case 'build':
    command = 'npx';
    args = ['next', 'build'];
    break;
  default:
    console.log('지원하지 않는 스크립트:', scriptType);
    process.exit(1);
}

console.log(`🚀 포트 ${frontendPort}에서 ${scriptType} 모드로 실행합니다...`);

const child = spawn(command, args, {
  stdio: 'inherit',
  shell: true
});

child.on('error', (error) => {
  console.error('프로세스 실행 에러:', error);
  process.exit(1);
});

child.on('close', (code) => {
  process.exit(code);
});
