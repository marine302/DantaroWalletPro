#!/usr/bin/env node

const net = require('net');
const { spawn, exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const http = require('http');

/**
 * 🚀 통합 서비스 관리자
 * 프론트엔드 개발 서버, 목업 HTTP 서버, 웹소켓 서버를 하나의 명령으로 관리
 */
class UnifiedServiceManager {
  constructor() {
    this.configFile = path.join(__dirname, '.service-config.json');
    this.lockFile = path.join(__dirname, '.services.lock');
    this.logFile = path.join(__dirname, 'services.log');
    
    this.defaultConfig = {
      ports: {
        frontend: 3020,
        mockHttp: 3001,
        mockWebSocket: 3002
      },
      services: {
        frontend: {
          name: 'Frontend Dev Server',
          command: 'npm',
          args: ['run', 'dev:frontend-only'],
          env: {},
          enabled: false, // 별도로 관리
          healthCheck: '/api/dashboard'
        },
        mockHttp: {
          name: 'Mock HTTP Server',
          command: 'node',
          args: ['mock-server.js'],
          env: {},
          enabled: true,
          healthCheck: '/health'
        },
        mockWebSocket: {
          name: 'Mock WebSocket Server',
          command: 'node',
          args: ['mock-realtime-server.js'],
          env: {},
          enabled: true,
          healthCheck: null // WebSocket은 HTTP health check 없음
        }
      }
    };
    
    this.processes = new Map();
    this.loadConfig();
    this.setupExitHandlers();
  }

  loadConfig() {
    try {
      if (fs.existsSync(this.configFile)) {
        const saved = JSON.parse(fs.readFileSync(this.configFile, 'utf8'));
        this.config = { ...this.defaultConfig, ...saved };
      } else {
        this.config = { ...this.defaultConfig };
        this.saveConfig();
      }
      this.syncWithEnv();
    } catch (error) {
      console.log('⚠️ 설정 파일 로드 실패, 기본값 사용');
      this.config = { ...this.defaultConfig };
    }
  }

  syncWithEnv() {
    const envPath = path.join(__dirname, '.env.local');
    if (fs.existsSync(envPath)) {
      const envContent = fs.readFileSync(envPath, 'utf8');
      
      // NEXT_PUBLIC_FRONTEND_PORT 확인
      const frontendPortMatch = envContent.match(/NEXT_PUBLIC_FRONTEND_PORT=(\d+)/);
      if (frontendPortMatch) {
        const envPort = parseInt(frontendPortMatch[1]);
        if (envPort !== this.config.ports.frontend) {
          this.config.ports.frontend = envPort;
          this.log(`📝 환경변수에서 프론트엔드 포트 업데이트: ${envPort}`);
        }
      }
      
      // NEXT_PUBLIC_WS_URL에서 WebSocket 포트 확인
      const wsUrlMatch = envContent.match(/NEXT_PUBLIC_WS_URL=ws:\/\/localhost:(\d+)/);
      if (wsUrlMatch) {
        const wsPort = parseInt(wsUrlMatch[1]);
        if (wsPort !== this.config.ports.mockWebSocket) {
          this.config.ports.mockWebSocket = wsPort;
          this.log(`📝 환경변수에서 WebSocket 포트 업데이트: ${wsPort}`);
        }
      }
      
      this.saveConfig();
    }
  }

  saveConfig() {
    try {
      fs.writeFileSync(this.configFile, JSON.stringify(this.config, null, 2));
    } catch (error) {
      console.error('❌ 설정 저장 실패:', error.message);
    }
  }

  log(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}\n`;
    console.log(message);
    
    try {
      fs.appendFileSync(this.logFile, logMessage);
    } catch (error) {
      // 로그 쓰기 실패는 무시
    }
  }

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

  async isServiceHealthy(serviceName) {
    const service = this.config.services[serviceName];
    const port = this.config.ports[serviceName];
    
    if (!service.healthCheck) {
      // WebSocket 같은 경우는 포트만 확인
      return await this.isPortInUse(port);
    }
    
    return new Promise((resolve) => {
      const req = http.get(`http://localhost:${port}${service.healthCheck}`, { 
        timeout: 3000 
      }, (res) => {
        resolve(res.statusCode < 500);
      });
      
      req.on('error', () => resolve(false));
      req.on('timeout', () => {
        req.destroy();
        resolve(false);
      });
    });
  }

  async findAvailablePort(startPort, maxTries = 10) {
    for (let i = 0; i < maxTries; i++) {
      const port = startPort + i;
      if (!(await this.isPortInUse(port))) {
        return port;
      }
    }
    throw new Error(`사용 가능한 포트를 찾을 수 없습니다 (시작: ${startPort})`);
  }

  async killProcessOnPort(port) {
    return new Promise((resolve) => {
      exec(`lsof -ti:${port}`, (error, stdout) => {
        if (error || !stdout.trim()) {
          resolve(false);
          return;
        }
        
        const pids = stdout.trim().split('\n');
        let killed = 0;
        
        pids.forEach(pid => {
          try {
            process.kill(parseInt(pid), 'SIGTERM');
            killed++;
          } catch (err) {
            // 프로세스가 이미 종료되었거나 권한 없음
          }
        });
        
        setTimeout(() => resolve(killed > 0), 1000);
      });
    });
  }

  updateEnvFile() {
    const envPath = path.join(__dirname, '.env.local');
    let envContent = '';
    
    if (fs.existsSync(envPath)) {
      envContent = fs.readFileSync(envPath, 'utf8');
    }
    
    // 포트 설정 업데이트
    const updates = [
      [`NEXT_PUBLIC_FRONTEND_PORT`, this.config.ports.frontend],
      [`NEXT_PUBLIC_API_URL`, `http://localhost:${this.config.ports.mockHttp}`],
      [`NEXT_PUBLIC_WS_URL`, `ws://localhost:${this.config.ports.mockWebSocket}`]
    ];
    
    updates.forEach(([key, value]) => {
      const regex = new RegExp(`^${key}=.*$`, 'm');
      const line = `${key}=${value}`;
      
      if (regex.test(envContent)) {
        envContent = envContent.replace(regex, line);
      } else {
        envContent += `\n${line}`;
      }
    });
    
    try {
      fs.writeFileSync(envPath, envContent.trim() + '\n');
      this.log(`📝 .env.local 업데이트 완료`);
    } catch (error) {
      console.error('❌ .env.local 업데이트 실패:', error.message);
    }
  }

  async startService(serviceName) {
    const service = this.config.services[serviceName];
    const port = this.config.ports[serviceName];
    
    if (!service.enabled) {
      this.log(`⏭️ ${service.name} 비활성화됨, 건너뛰기`);
      return false;
    }
    
    // 이미 실행 중인지 확인
    if (await this.isServiceHealthy(serviceName)) {
      this.log(`✅ ${service.name} 이미 실행 중 (포트: ${port})`);
      return true;
    }
    
    // 포트 사용 중이면 처리
    if (await this.isPortInUse(port)) {
      this.log(`⚠️ 포트 ${port} 사용 중, 프로세스 종료 시도...`);
      await this.killProcessOnPort(port);
      
      // 잠시 대기 후 다시 확인
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      if (await this.isPortInUse(port)) {
        // 다른 포트 찾기
        const newPort = await this.findAvailablePort(port + 1);
        this.log(`🔄 새 포트로 변경: ${port} → ${newPort}`);
        this.config.ports[serviceName] = newPort;
        this.saveConfig();
      }
    }
    
    // 서비스 시작
    const env = {
      ...process.env,
      ...service.env,
      PORT: this.config.ports[serviceName]
    };
    
    if (serviceName === 'frontend') {
      env.PORT = this.config.ports.frontend;
    }
    
    this.log(`🚀 ${service.name} 시작 중... (포트: ${this.config.ports[serviceName]})`);
    
    const childProcess = spawn(service.command, service.args, {
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
      cwd: __dirname
    });
    
    this.processes.set(serviceName, childProcess);
    
    // 출력 로깅
    childProcess.stdout.on('data', (data) => {
      const output = data.toString().trim();
      if (output) {
        this.log(`[${service.name}] ${output}`);
      }
    });
    
    childProcess.stderr.on('data', (data) => {
      const output = data.toString().trim();
      if (output) {
        this.log(`[${service.name}] ERROR: ${output}`);
      }
    });
    
    childProcess.on('exit', (code) => {
      this.log(`❌ ${service.name} 종료됨 (코드: ${code})`);
      this.processes.delete(serviceName);
    });
    
    // 시작 확인
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    if (await this.isServiceHealthy(serviceName)) {
      this.log(`✅ ${service.name} 시작 완료`);
      return true;
    } else {
      this.log(`❌ ${service.name} 시작 실패`);
      return false;
    }
  }

  async stopService(serviceName) {
    const process = this.processes.get(serviceName);
    const service = this.config.services[serviceName];
    
    if (process) {
      this.log(`🛑 ${service.name} 종료 중...`);
      process.kill('SIGTERM');
      
      // 강제 종료 대기
      setTimeout(() => {
        if (!process.killed) {
          process.kill('SIGKILL');
        }
      }, 5000);
      
      this.processes.delete(serviceName);
    }
    
    // 포트에서 실행 중인 다른 프로세스도 종료
    await this.killProcessOnPort(this.config.ports[serviceName]);
  }

  async startAll() {
    this.log('🚀 모든 서비스 시작 중...');
    
    // 환경 파일 업데이트
    this.updateEnvFile();
    
    // 락 파일 생성
    fs.writeFileSync(this.lockFile, JSON.stringify({
      pid: process.pid,
      started: new Date().toISOString(),
      ports: this.config.ports
    }));
    
    const results = [];
    
    // 서비스들을 순서대로 시작 (의존성 고려)
    for (const serviceName of ['mockHttp', 'mockWebSocket']) {
      const success = await this.startService(serviceName);
      results.push({ service: serviceName, success });
    }
    
    // 결과 요약
    const successful = results.filter(r => r.success).length;
    const total = results.length;
    
    this.log(`\n📊 서비스 시작 완료: ${successful}/${total}`);
    
    if (successful > 0) {
      this.log('\n🌐 접속 정보:');
      if (this.config.services.frontend.enabled && results.find(r => r.service === 'frontend')?.success) {
        this.log(`   Frontend: http://localhost:${this.config.ports.frontend}`);
      }
      if (this.config.services.mockHttp.enabled && results.find(r => r.service === 'mockHttp')?.success) {
        this.log(`   Mock API: http://localhost:${this.config.ports.mockHttp}`);
      }
      if (this.config.services.mockWebSocket.enabled && results.find(r => r.service === 'mockWebSocket')?.success) {
        this.log(`   WebSocket: ws://localhost:${this.config.ports.mockWebSocket}`);
      }
      this.log('\n💡 종료하려면 Ctrl+C를 누르세요');
    }
    
    return successful === total;
  }

  async stopAll() {
    this.log('🛑 모든 서비스 종료 중...');
    
    for (const serviceName of this.processes.keys()) {
      await this.stopService(serviceName);
    }
    
    // 락 파일 제거
    if (fs.existsSync(this.lockFile)) {
      fs.unlinkSync(this.lockFile);
    }
    
    this.log('✅ 모든 서비스 종료 완료');
  }

  async getStatus() {
    const status = {
      running: [],
      stopped: [],
      ports: this.config.ports,
      healthy: true
    };
    
    for (const [serviceName, service] of Object.entries(this.config.services)) {
      const isHealthy = await this.isServiceHealthy(serviceName);
      const port = this.config.ports[serviceName];
      
      if (isHealthy) {
        status.running.push({
          name: serviceName,
          displayName: service.name,
          port,
          url: service.healthCheck ? `http://localhost:${port}${service.healthCheck}` : null
        });
      } else {
        status.stopped.push({
          name: serviceName,
          displayName: service.name,
          port
        });
        status.healthy = false;
      }
    }
    
    return status;
  }

  setupExitHandlers() {
    const exitHandler = (signal) => {
      this.log(`\n📡 ${signal} 신호 수신, 정리 중...`);
      this.stopAll().then(() => {
        process.exit(0);
      });
    };
    
    process.on('SIGINT', () => exitHandler('SIGINT'));
    process.on('SIGTERM', () => exitHandler('SIGTERM'));
    process.on('SIGQUIT', () => exitHandler('SIGQUIT'));
  }
}

// CLI 인터페이스
async function main() {
  const manager = new UnifiedServiceManager();
  const command = process.argv[2] || 'start';
  
  switch (command) {
    case 'start':
    case 'dev':
      await manager.startAll();
      // 프로세스를 계속 실행
      setInterval(() => {}, 1000);
      break;
      
    case 'stop':
      await manager.stopAll();
      process.exit(0);
      break;
      
    case 'status':
      const status = await manager.getStatus();
      console.log('\n📊 서비스 상태:');
      
      if (status.running.length > 0) {
        console.log('\n✅ 실행 중:');
        status.running.forEach(service => {
          console.log(`   ${service.displayName}: http://localhost:${service.port}`);
        });
      }
      
      if (status.stopped.length > 0) {
        console.log('\n❌ 중지됨:');
        status.stopped.forEach(service => {
          console.log(`   ${service.displayName}: 포트 ${service.port}`);
        });
      }
      
      console.log(`\n전체 상태: ${status.healthy ? '정상' : '일부 문제'}`);
      break;
      
    case 'restart':
      await manager.stopAll();
      await new Promise(resolve => setTimeout(resolve, 2000));
      await manager.startAll();
      setInterval(() => {}, 1000);
      break;
      
    case 'config':
      console.log('\n⚙️ 현재 설정:');
      console.log(JSON.stringify(manager.config, null, 2));
      break;
      
    default:
      console.log(`
🚀 통합 서비스 관리자

사용법:
  node unified-service-manager.js [command]

명령어:
  start     모든 서비스 시작 (기본값)
  dev       개발 모드로 모든 서비스 시작 (start와 동일)
  stop      모든 서비스 중지
  restart   모든 서비스 재시작
  status    서비스 상태 확인
  config    현재 설정 표시

관리되는 서비스:
  - Frontend Dev Server (Next.js)
  - Mock HTTP Server
  - Mock WebSocket Server
      `);
      break;
  }
}

if (require.main === module) {
  main().catch(error => {
    console.error('❌ 오류 발생:', error.message);
    process.exit(1);
  });
}

module.exports = UnifiedServiceManager;
