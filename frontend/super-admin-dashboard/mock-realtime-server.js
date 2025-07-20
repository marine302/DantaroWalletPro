const WebSocket = require('ws');
const express = require('express');
const cors = require('cors');

// HTTP 서버 설정
const app = express();
app.use(cors());
app.use(express.json());

// Mock 데이터 생성 함수들
function generateSystemStats() {
  return {
    cpuUsage: Math.random() * 100,
    memoryUsage: Math.random() * 100,
    diskUsage: Math.random() * 100,
    activeConnections: Math.floor(Math.random() * 1000) + 100
  };
}

function generateDashboardStats() {
  return {
    activeUsers: Math.floor(Math.random() * 50) + 10,
    totalTransactions: Math.floor(Math.random() * 10000) + 1000,
    energyTrading: Math.floor(Math.random() * 500) + 100,
    revenue: Math.floor(Math.random() * 100000) + 10000
  };
}

function generateAlert() {
  const types = ['error', 'warning', 'info'];
  const messages = [
    'High CPU usage detected',
    'Low disk space warning',
    'New user registration',
    'Energy trade completed',
    'System backup completed',
    'Network latency spike',
    'Database connection restored'
  ];
  
  return {
    id: Date.now().toString(),
    type: types[Math.floor(Math.random() * types.length)],
    message: messages[Math.floor(Math.random() * messages.length)],
    timestamp: new Date().toISOString()
  };
}

function generateEnergyMarket() {
  const basePrice = 120;
  const change = (Math.random() - 0.5) * 20;
  
  return {
    currentPrice: basePrice + change,
    priceChange: change,
    volume: Math.floor(Math.random() * 10000) + 1000,
    providers: [
      {
        id: '1',
        name: 'GreenEnergy Corp',
        status: Math.random() > 0.2 ? 'online' : 'offline',
        price: basePrice + (Math.random() - 0.5) * 10
      },
      {
        id: '2',
        name: 'SolarPower Ltd',
        status: Math.random() > 0.2 ? 'online' : 'offline',
        price: basePrice + (Math.random() - 0.5) * 10
      },
      {
        id: '3',
        name: 'WindTech Solutions',
        status: Math.random() > 0.2 ? 'online' : 'offline',
        price: basePrice + (Math.random() - 0.5) * 10
      }
    ]
  };
}

function generateTransaction() {
  const types = ['energy_purchase', 'energy_sale', 'wallet_deposit', 'wallet_withdrawal'];
  const statuses = ['pending', 'completed', 'failed'];
  
  return {
    id: Date.now().toString(),
    type: types[Math.floor(Math.random() * types.length)],
    amount: Math.floor(Math.random() * 1000) + 10,
    status: statuses[Math.floor(Math.random() * statuses.length)],
    timestamp: new Date().toISOString()
  };
}

// HTTP API 엔드포인트
app.get('/api/dashboard/stats', (req, res) => {
  res.json({
    systemStats: generateSystemStats(),
    dashboardStats: generateDashboardStats(),
    energyMarket: generateEnergyMarket()
  });
});

const httpPort = 3001;
app.listen(httpPort, () => {
  console.log(`🚀 Mock HTTP Server running on port ${httpPort}`);
});

// WebSocket 서버 설정
const wss = new WebSocket.Server({ port: 3002 });

console.log('🔌 Mock WebSocket Server running on port 3002');

// 연결된 클라이언트들
const clients = new Set();

wss.on('connection', (ws) => {
  console.log('Client connected');
  clients.add(ws);

  // 연결 시 초기 데이터 전송
  ws.send(JSON.stringify({
    type: 'systemStats',
    data: generateSystemStats(),
    timestamp: new Date().toISOString()
  }));

  ws.send(JSON.stringify({
    type: 'dashboardStats',
    data: generateDashboardStats(),
    timestamp: new Date().toISOString()
  }));

  ws.send(JSON.stringify({
    type: 'energyMarket',
    data: generateEnergyMarket(),
    timestamp: new Date().toISOString()
  }));

  // Ping 메시지 응답
  ws.on('message', (message) => {
    try {
      const parsed = JSON.parse(message);
      if (parsed.type === 'ping') {
        ws.send(JSON.stringify({ type: 'pong', timestamp: new Date().toISOString() }));
      }
    } catch (error) {
      console.error('Failed to parse message:', error);
    }
  });

  ws.on('close', () => {
    console.log('Client disconnected');
    clients.delete(ws);
  });

  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
    clients.delete(ws);
  });
});

// 주기적으로 데이터 브로드캐스트
function broadcastToClients(type, data) {
  const message = JSON.stringify({
    type,
    data,
    timestamp: new Date().toISOString()
  });

  clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(message);
    }
  });
}

// 시스템 통계 업데이트 (5초마다)
setInterval(() => {
  broadcastToClients('systemStats', generateSystemStats());
}, 5000);

// 대시보드 통계 업데이트 (10초마다)
setInterval(() => {
  broadcastToClients('dashboardStats', generateDashboardStats());
}, 10000);

// 에너지 마켓 데이터 업데이트 (7초마다)
setInterval(() => {
  broadcastToClients('energyMarket', generateEnergyMarket());
}, 7000);

// 랜덤 알림 생성 (15-30초마다)
setInterval(() => {
  if (Math.random() > 0.3) {
    broadcastToClients('alert', generateAlert());
  }
}, Math.random() * 15000 + 15000);

// 랜덤 트랜잭션 생성 (5-15초마다)
setInterval(() => {
  if (Math.random() > 0.4) {
    broadcastToClients('transaction', generateTransaction());
  }
}, Math.random() * 10000 + 5000);

console.log('📊 Mock data broadcasting started');
console.log('   - System stats: every 5s');
console.log('   - Dashboard stats: every 10s');
console.log('   - Energy market: every 7s');
console.log('   - Random alerts: every 15-30s');
console.log('   - Random transactions: every 5-15s');
