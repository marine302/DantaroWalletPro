#!/usr/bin/env node

const net = require('net');
const { spawn, exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const http = require('http');

/**
 * 🚀 스마트 포트 관리자 (백엔드 dev-manager.sh 방식 적용)
 * - 서버가 이미 실행 중이면 기존 서버 활용
 * - 포트 충돌 시 자동으로 다음 포트 찾기 또는 기존 프로세스 종료 선택
 * - 중복 실행 방지
 * - 정상 종료 처리
 * - Health 체크 우선 로직
 */
class SmartPortManager {
  constructor() {
    this.configFile = path.join(__dirname, '.port-config.json');
    this.lockFile = path.join(__dirname, '.server.lock');
    this.defaultPorts = {
      frontend: 3020,
      mockHttp: 3001,
      mockWebSocket: 3002
    };
    this.loadConfig();
  }

  loadConfig() {
    try {
      if (fs.existsSync(this.configFile)) {
        this.config = JSON.parse(fs.readFileSync(this.configFile, 'utf8'));
      } else {
        this.config = { ...this.defaultPorts };
        this.saveConfig();
      }
      
      // .env.local에서 포트 확인
      this.checkEnvPort();
    } catch (error) {
      console.log('⚠️ 포트 설정 파일 로드 실패, 기본값 사용');
      this.config = { ...this.defaultPorts };
    }
  }

  checkEnvPort() {
    const envPath = path.join(__dirname, '.env.local');
    if (fs.existsSync(envPath)) {
      const envContent = fs.readFileSync(envPath, 'utf8');
      const match = envContent.match(/NEXT_PUBLIC_FRONTEND_PORT=(\d+)/);
      if (match) {
        const envPort = parseInt(match[1]);
        if (envPort !== this.config.frontend) {
          this.config.frontend = envPort;
          this.saveConfig();
        }
      }
    }
  }

  saveConfig() {
    try {
      fs.writeFileSync(this.configFile, JSON.stringify(this.config, null, 2));
    } catch (error) {
      console.error('❌ 포트 설정 저장 실패:', error.message);
    }
  }

  /**
   * 포트가 사용 중인지 확인
   */
  async isPortInUse(port) {
    return new Promise((resolve) => {
      const server = net.createServer();
      server.listen(port, (err) => {
        if (err) {
          resolve(true);
        } else {
          server.once('close', () => resolve(false));
          server.close();
        }
      });
      server.on('error', () => resolve(true));
    });
  }

  /**
   * 서버가 실제로 응답하는지 확인 (백엔드 방식과 동일)
   */
  async isServerResponding(port) {
    return new Promise((resolve) => {
      const req = http.get(`http://localhost:${port}`, { timeout: 3000 }, (res) => {
        resolve(res.statusCode < 500); // 500 미만이면 정상 응답
      });
      
      req.on('error', () => resolve(false));
      req.on('timeout', () => {
        req.destroy();
        resolve(false);
      });
    });
  }

  /**
   * 사용 가능한 포트 찾기
   */
  async findAvailablePort(startPort) {
    let port = startPort;
    let attempts = 0;
    const maxAttempts = 50;
    
    while (await this.isPortInUse(port) && attempts < maxAttempts) {
      port++;
      attempts++;
    }
    
    if (attempts >= maxAttempts) {
      throw new Error(`❌ 포트 ${startPort}부터 ${port}까지 모두 사용 중입니다.`);
    }
    
    return port;
  }

  /**
   * 포트의 프로세스 안전하게 종료
   */
  async killProcessOnPort(port) {
    return new Promise((resolve) => {
      exec(`lsof -ti:${port}`, (error, stdout) => {
        if (error || !stdout.trim()) {
          resolve(false);
          return;
        }
        
        const pids = stdout.trim().split('\n');
        let killCount = 0;
        
        console.log(`🔄 포트 ${port}의 프로세스들을 종료합니다...`);
        
        pids.forEach(pid => {
          try {
            process.kill(parseInt(pid), 'SIGTERM');
            killCount++;
            console.log(`   💀 PID ${pid} 종료 신호 전송`);
          } catch (e) {
            console.log(`   ⚠️ PID ${pid} 종료 실패: ${e.message}`);
          }
        });
        
        // SIGTERM 후 잠시 대기하고 SIGKILL
        setTimeout(() => {
          pids.forEach(pid => {
            try {
              process.kill(parseInt(pid), 'SIGKILL');
            } catch (e) {
              // 이미 종료된 경우 무시
            }
          });
          resolve(killCount > 0);
        }, 2000);
      });
    });
  }

  /**
   * 서버 중복 실행 확인 (백엔드 방식)
   */
  isServerAlreadyRunning() {
    if (!fs.existsSync(this.lockFile)) {
      return false;
    }
    
    try {
      const lockData = JSON.parse(fs.readFileSync(this.lockFile, 'utf8'));
      const { pid, port, timestamp } = lockData;
      
      // 프로세스가 실제로 실행 중인지 확인
      try {
        process.kill(pid, 0);
        console.log(`✅ 서버가 이미 실행 중입니다 (PID: ${pid}, 포트: ${port})`);
        console.log(`🌐 접속 주소: http://localhost:${port}`);
        console.log(`⏰ 시작 시간: ${new Date(timestamp).toLocaleString()}`);
        return { pid, port, timestamp };
      } catch (e) {
        // 프로세스가 없으면 락 파일 제거
        fs.unlinkSync(this.lockFile);
        return false;
      }
    } catch (e) {
      fs.unlinkSync(this.lockFile);
      return false;
    }
  }

  /**
   * 서버 락 파일 생성
   */
  createServerLock(port) {
    const lockData = {
      pid: process.pid,
      port: port,
      timestamp: new Date().toISOString(),
      command: process.argv.join(' '),
      cwd: __dirname
    };
    
    try {
      fs.writeFileSync(this.lockFile, JSON.stringify(lockData, null, 2));
      console.log(`🔒 서버 락 파일 생성됨 (PID: ${process.pid}, 포트: ${port})`);
    } catch (error) {
      console.warn('⚠️ 락 파일 생성 실패:', error.message);
    }
  }

  /**
   * 정리 함수
   */
  cleanup() {
    try {
      if (fs.existsSync(this.lockFile)) {
        const lockData = JSON.parse(fs.readFileSync(this.lockFile, 'utf8'));
        if (lockData.pid === process.pid) {
          fs.unlinkSync(this.lockFile);
          console.log('🧹 락 파일 정리됨');
        }
      }
    } catch (error) {
      console.warn('⚠️ 정리 실패:', error.message);
    }
  }

  /**
   * 포트 상태 표시
   */
  async showPortStatus() {
    console.log('\n📊 포트 사용 현황:');
    const ports = [this.config.frontend, 3000, 3001, 3020, 3030, 8000];
    
    for (const port of ports) {
      const inUse = await this.isPortInUse(port);
      const responding = inUse ? await this.isServerResponding(port) : false;
      
      let status = '🟢 사용 가능';
      if (inUse && responding) {
        status = '🔵 실행 중 (응답함)';
      } else if (inUse) {
        status = '🟡 사용 중 (응답 없음)';
      }
      
      console.log(`   포트 ${port}: ${status}`);
    }
    console.log('');
  }

  /**
   * 메인 실행 함수 (백엔드 start_frontend_server 방식)
   */
  async run(mode = 'dev') {
    console.log(`🚀 포트 ${this.config.frontend}에서 ${mode} 모드로 실행합니다...`);
    
    // 1. 이미 실행 중인 서버 확인 (백엔드 방식과 동일)
    const existingServer = this.isServerAlreadyRunning();
    if (existingServer) {
      const { port } = existingServer;
      
      // 서버가 실제로 응답하는지 확인
      console.log('🔍 서버 응답 확인 중...');
      if (await this.isServerResponding(port)) {
        console.log(`✅ 기존 서버가 정상 동작 중입니다. 새로 시작하지 않습니다.`);
        console.log(`🌐 브라우저에서 http://localhost:${port} 를 확인하세요.`);
        return;
      } else {
        console.log(`⚠️ 서버는 실행 중이지만 응답하지 않습니다. 재시작합니다.`);
        await this.killProcessOnPort(port);
        this.cleanup();
        await new Promise(resolve => setTimeout(resolve, 3000)); // 3초 대기
      }
    }
    
    // 2. 포트 상태 확인 및 표시
    await this.showPortStatus();
    
    // 3. 타겟 포트 결정
    let targetPort = this.config.frontend;
    
    if (await this.isPortInUse(targetPort)) {
      console.log(`⚠️ 포트 ${targetPort}이 다른 프로세스에 의해 사용 중입니다.`);
      
      // 자동으로 다음 포트 찾기
      const newPort = await this.findAvailablePort(targetPort + 1);
      console.log(`🔍 자동으로 포트 ${newPort}을 사용합니다.`);
      targetPort = newPort;
      
      // 설정 업데이트
      this.config.frontend = targetPort;
      this.saveConfig();
      this.updateEnvFile(targetPort);
    }
    
    // 4. 서버 시작
    this.createServerLock(targetPort);
    await this.startNextServer(mode, targetPort);
  }

  /**
   * .env.local 파일 업데이트
   */
  updateEnvFile(port) {
    const envPath = path.join(__dirname, '.env.local');
    let envContent = '';
    
    if (fs.existsSync(envPath)) {
      envContent = fs.readFileSync(envPath, 'utf8');
      if (envContent.includes('NEXT_PUBLIC_FRONTEND_PORT=')) {
        envContent = envContent.replace(/NEXT_PUBLIC_FRONTEND_PORT=\d+/, `NEXT_PUBLIC_FRONTEND_PORT=${port}`);
      } else {
        envContent += `\nNEXT_PUBLIC_FRONTEND_PORT=${port}\n`;
      }
    } else {
      envContent = `NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Super Admin Dashboard
NEXT_PUBLIC_FRONTEND_PORT=${port}
PORT=${port}
`;
    }
    
    fs.writeFileSync(envPath, envContent);
    console.log(`📝 .env.local 포트 업데이트: ${port}`);
  }

  /**
   * Next.js 서버 시작
   */
  async startNextServer(mode, port) {
    const env = { 
      ...process.env, 
      PORT: port.toString(),
      NODE_ENV: mode === 'build' ? 'production' : 'development'
    };
    
    // Turbopack 사용
    let command, args;
    switch (mode) {
      case 'dev':
        command = 'npx';
        args = ['next', 'dev', '--turbopack', '-p', port.toString()];
        break;
      case 'start':
        command = 'npx';
        args = ['next', 'start', '-p', port.toString()];
        break;
      case 'build':
        command = 'npx';
        args = ['next', 'build'];
        break;
      default:
        throw new Error(`지원하지 않는 모드: ${mode}`);
    }
    
    console.log(`🎯 실행: ${command} ${args.join(' ')}`);
    console.log(`🌐 서버 주소: http://localhost:${port}`);
    console.log(`🔧 모드: ${mode}`);
    
    const child = spawn(command, args, { 
      stdio: 'inherit', 
      env,
      cwd: __dirname
    });
    
    // 정리 핸들러 등록
    const cleanup = () => {
      console.log('\n🛑 서버를 종료합니다...');
      this.cleanup();
      child.kill('SIGTERM');
      setTimeout(() => {
        child.kill('SIGKILL');
        process.exit(0);
      }, 5000);
    };
    
    process.on('SIGINT', cleanup);
    process.on('SIGTERM', cleanup);
    process.on('exit', () => this.cleanup());
    
    child.on('error', (error) => {
      console.error('❌ 서버 시작 실패:', error.message);
      this.cleanup();
      process.exit(1);
    });
    
    child.on('exit', (code) => {
      console.log(`서버 종료 (코드: ${code})`);
      this.cleanup();
      process.exit(code || 0);
    });
  }

  /**
   * 포트 상태만 확인
   */
  async status() {
    console.log('🔍 서버 상태 확인 중...');
    
    const existingServer = this.isServerAlreadyRunning();
    if (existingServer) {
      const { port } = existingServer;
      const responding = await this.isServerResponding(port);
      console.log(`서버 응답: ${responding ? '✅ 정상' : '❌ 응답 없음'}`);
    } else {
      console.log('❌ 실행 중인 서버가 없습니다.');
    }
    
    await this.showPortStatus();
  }

  /**
   * 모든 관련 프로세스 종료
   */
  async stop() {
    console.log('🛑 모든 관련 서버를 종료합니다...');
    
    const ports = [this.config.frontend, 3020, 3000];
    for (const port of ports) {
      if (await this.isPortInUse(port)) {
        console.log(`🔄 포트 ${port} 정리 중...`);
        await this.killProcessOnPort(port);
      }
    }
    
    this.cleanup();
    console.log('✅ 종료 완료');
  }
}

// =============================================================================
// 메인 실행 부분
// =============================================================================

async function main() {
  const args = process.argv.slice(2);
  const command = args[0] || 'dev';
  
  const manager = new SmartPortManager();
  
  try {
    switch (command) {
      case 'dev':
      case 'start':
      case 'build':
        await manager.run(command);
        break;
      case 'status':
        await manager.status();
        break;
      case 'stop':
        await manager.stop();
        break;
      case 'ports':
        await manager.showPortStatus();
        break;
      default:
        console.log(`
🚀 스마트 포트 관리자 사용법:

  node smart-port-manager.js [명령어]

명령어:
  dev      개발 서버 시작 (기본값)
  start    프로덕션 서버 시작  
  build    빌드만 실행
  status   서버 상태 확인
  stop     모든 서버 종료
  ports    포트 사용 현황

특징:
  ✅ 기존 서버가 실행 중이면 재사용
  ✅ 포트 충돌 시 자동으로 다른 포트 사용
  ✅ 안전한 프로세스 종료
  ✅ Health 체크 우선 로직
`);
        break;
    }
  } catch (error) {
    console.error('❌ 실행 실패:', error.message);
    manager.cleanup();
    process.exit(1);
  }
}

// 스크립트가 직접 실행된 경우에만 main 함수 호출
if (require.main === module) {
  main().catch(console.error);
}

module.exports = SmartPortManager;
