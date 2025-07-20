#!/usr/bin/env node

/**
 * 파트너 어드민 포트 설정을 중앙에서 관리하는 스크립트
 * .env.local에서 NEXT_PUBLIC_FRONTEND_PORT를 읽어서 사용
 */

const fs = require('fs');
const path = require('path');

// .env.local 파일 읽기
const envPath = path.join(__dirname, '.env.local');
let frontendPort = 3030; // 파트너 어드민 기본 포트

if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf8');
    const match = envContent.match(/NEXT_PUBLIC_FRONTEND_PORT=(\d+)/);
    if (match) {
        frontendPort = parseInt(match[1]);
    }
}

console.log(`🚀 Partner Admin Template 포트: ${frontendPort}`);

// 환경변수 설정
process.env.PORT = frontendPort.toString();

// Next.js 명령어 실행
const { spawn } = require('child_process');

const command = process.argv[2] || 'dev';
const args = process.argv.slice(3);

let nextCommand;
switch (command) {
    case 'dev':
        nextCommand = 'next';
        args.unshift('dev', '--port', frontendPort.toString());
        break;
    case 'build':
        nextCommand = 'next';
        args.unshift('build');
        break;
    case 'start':
        nextCommand = 'next';
        args.unshift('start', '--port', frontendPort.toString());
        break;
    default:
        console.error(`Unknown command: ${command}`);
        process.exit(1);
}

const child = spawn(nextCommand, args, {
    stdio: 'inherit',
    shell: process.platform === 'win32'
});

child.on('close', (code) => {
    process.exit(code);
});
