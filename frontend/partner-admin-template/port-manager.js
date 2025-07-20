#!/usr/bin/env node

/**
 * DantaroWallet 파트너 관리자 포트 매니저
 * 
 * 📋 DantaroWallet 프로젝트 표준 포트 설정:
 * - 🔧 백엔드 API 서버: 8000 (FastAPI + Uvicorn)
 * - 🔒 Super Admin Dashboard: 3020 (Next.js)  
 * - ⚛️ Partner Admin Template: 3030 (Next.js) ← 이 프로젝트
 * 
 * ⚠️ 중요: 이 포트들은 dev-manager.sh와 완전히 동기화되어 있습니다
 * 절대로 임의로 변경하지 마세요!
 */

const fs = require('fs');
const path = require('path');

// DantaroWallet 프로젝트 표준 포트 (dev-manager.sh와 동일)
const PORT_STANDARD = {
  BACKEND_API: 8000,        // FastAPI 백엔드 서버
  SUPER_ADMIN: 3020,        // Super Admin Dashboard  
  PARTNER_ADMIN: 3030,      // Partner Admin Template (이 프로젝트)
};

// 이 프로젝트의 고정 포트
const FIXED_PORT = PORT_STANDARD.PARTNER_ADMIN;
const SERVICE_NAME = "Partner Admin Template";

console.log(`🚀 ${SERVICE_NAME} 포트: ${FIXED_PORT}`);
console.log(`📋 DantaroWallet 표준 포트 - 백엔드:${PORT_STANDARD.BACKEND_API}, Super:${PORT_STANDARD.SUPER_ADMIN}, Partner:${PORT_STANDARD.PARTNER_ADMIN}`);

// .env.local 파일에서 포트 확인 및 강제 설정
const envPath = path.join(__dirname, '.env.local');
let shouldUpdateEnv = false;

if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf8');
    
    // 포트가 다르게 설정되어 있다면 경고하고 고정 포트로 강제 설정
    const portMatch = envContent.match(/NEXT_PUBLIC_FRONTEND_PORT=(\d+)/);
    if (portMatch && parseInt(portMatch[1]) !== FIXED_PORT) {
        console.warn(`⚠️  경고: .env.local의 포트가 ${portMatch[1]}로 설정되어 있습니다.`);
        console.warn(`⚠️  파트너 어드민은 반드시 포트 ${FIXED_PORT}를 사용해야 합니다.`);
        console.warn(`⚠️  포트를 ${FIXED_PORT}로 강제 변경합니다.`);
        shouldUpdateEnv = true;
    }
    
    const basicPortMatch = envContent.match(/^PORT=(\d+)/m);
    if (basicPortMatch && parseInt(basicPortMatch[1]) !== FIXED_PORT) {
        shouldUpdateEnv = true;
    }
    
    if (shouldUpdateEnv) {
        let updatedContent = envContent
            .replace(/NEXT_PUBLIC_FRONTEND_PORT=\d+/, `NEXT_PUBLIC_FRONTEND_PORT=${FIXED_PORT}`)
            .replace(/^PORT=\d+/m, `PORT=${FIXED_PORT}`);
        
        if (!envContent.includes('PORT=')) {
            updatedContent += `\nPORT=${FIXED_PORT}\n`;
        }
        
        fs.writeFileSync(envPath, updatedContent);
        console.log(`✅ .env.local 포트를 ${FIXED_PORT}로 수정했습니다.`);
    }
} else {
    console.warn(`⚠️  .env.local 파일이 없습니다. .env.example을 복사해서 생성하세요.`);
}

// 환경변수 강제 설정
process.env.PORT = FIXED_PORT.toString();
process.env.NEXT_PUBLIC_FRONTEND_PORT = FIXED_PORT.toString();

// Next.js 명령어 실행
const { spawn } = require('child_process');

const command = process.argv[2] || 'dev';
const args = process.argv.slice(3);

let nextCommand;
switch (command) {
    case 'dev':
        nextCommand = 'next';
        args.unshift('dev', '--port', FIXED_PORT.toString());
        break;
    case 'build':
        nextCommand = 'next';
        args.unshift('build');
        break;
    case 'start':
        nextCommand = 'next';
        args.unshift('start', '--port', FIXED_PORT.toString());
        break;
    default:
        console.error(`❌ 알 수 없는 명령어: ${command}`);
        console.error(`사용 가능한 명령어: dev, build, start`);
        process.exit(1);
}

// 포트 충돌 검사
const net = require('net');

function checkPortAvailable(port) {
    return new Promise((resolve) => {
        const server = net.createServer();
        server.listen(port, () => {
            server.once('close', () => resolve(true));
            server.close();
        });
        server.on('error', () => resolve(false));
    });
}

// Next.js 프로세스 시작
async function startNextProcess() {
    // 포트 사용 가능 여부 확인
    const isPortAvailable = await checkPortAvailable(FIXED_PORT);
    if (!isPortAvailable) {
        console.error(`❌ 포트 ${FIXED_PORT}가 이미 사용 중입니다.`);
        console.error(`다른 파트너 어드민 인스턴스가 실행 중이거나 다른 서비스가 해당 포트를 사용하고 있습니다.`);
        console.error(`포트 ${FIXED_PORT}를 사용하는 프로세스를 종료하고 다시 시도하세요.`);
        process.exit(1);
    }

    console.log(`✅ 포트 ${FIXED_PORT} 사용 가능 확인됨`);
    
    const child = spawn(nextCommand, args, {
        stdio: 'inherit',
        shell: process.platform === 'win32'
    });

    child.on('error', (error) => {
        console.error(`❌ 프로세스 시작 실패:`, error);
        process.exit(1);
    });

    child.on('close', (code) => {
        if (code !== 0) {
            console.error(`❌ 프로세스가 코드 ${code}로 종료되었습니다.`);
        }
        process.exit(code);
    });

    // 프로세스 종료 시 정리
    process.on('SIGINT', () => {
        console.log(`\n🛑 ${SERVICE_NAME} 서버를 종료합니다...`);
        child.kill('SIGINT');
    });

    process.on('SIGTERM', () => {
        console.log(`\n🛑 ${SERVICE_NAME} 서버를 종료합니다...`);
        child.kill('SIGTERM');
    });
}

// 실행
startNextProcess().catch((error) => {
    console.error(`❌ 서버 시작 실패:`, error);
    process.exit(1);
});
