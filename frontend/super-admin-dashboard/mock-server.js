const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// Mock 데이터 생성 함수들
function generateDashboardStats() {
  return {
    activeUsers: Math.floor(Math.random() * 50) + 10,
    totalTransactions: Math.floor(Math.random() * 10000) + 1000,
    energyTrading: Math.floor(Math.random() * 500) + 100,
    revenue: Math.floor(Math.random() * 100000) + 10000,
    systemHealth: Math.random() > 0.8 ? 'warning' : 'healthy',
    lastUpdated: new Date().toISOString()
  };
}

function generateUserList() {
  const users = [];
  const roles = ['super-admin', 'partner-admin', 'viewer'];
  const statuses = ['active', 'inactive', 'pending'];
  
  for (let i = 1; i <= 20; i++) {
    users.push({
      id: i,
      name: `User ${i}`,
      email: `user${i}@example.com`,
      role: roles[Math.floor(Math.random() * roles.length)],
      status: statuses[Math.floor(Math.random() * statuses.length)],
      lastLogin: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
      createdAt: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString()
    });
  }
  
  return users;
}

function generatePartnerList() {
  const partners = [];
  const statuses = ['active', 'pending', 'suspended'];
  
  for (let i = 1; i <= 15; i++) {
    partners.push({
      id: i,
      name: `Partner Company ${i}`,
      type: Math.random() > 0.5 ? 'energy-provider' : 'consumer',
      status: statuses[Math.floor(Math.random() * statuses.length)],
      totalTransactions: Math.floor(Math.random() * 1000),
      revenue: Math.floor(Math.random() * 50000),
      onboardedAt: new Date(Date.now() - Math.random() * 180 * 24 * 60 * 60 * 1000).toISOString()
    });
  }
  
  return partners;
}

function generateTransactionHistory() {
  const transactions = [];
  const types = ['energy-purchase', 'energy-sale', 'fee-payment', 'withdrawal'];
  const statuses = ['completed', 'pending', 'failed'];
  
  for (let i = 1; i <= 50; i++) {
    transactions.push({
      id: `tx_${i}`,
      type: types[Math.floor(Math.random() * types.length)],
      amount: Math.floor(Math.random() * 10000) + 100,
      currency: 'KRW',
      status: statuses[Math.floor(Math.random() * statuses.length)],
      partnerId: Math.floor(Math.random() * 15) + 1,
      timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString()
    });
  }
  
  return transactions.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
}

function generateAnalyticsData() {
  return {
    daily: Array.from({ length: 30 }, (_, i) => ({
      date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      transactions: Math.floor(Math.random() * 100) + 50,
      revenue: Math.floor(Math.random() * 50000) + 10000,
      activeUsers: Math.floor(Math.random() * 20) + 10
    })),
    monthly: Array.from({ length: 12 }, (_, i) => ({
      month: new Date(2024, i, 1).toISOString().split('T')[0],
      transactions: Math.floor(Math.random() * 3000) + 1000,
      revenue: Math.floor(Math.random() * 1000000) + 500000,
      activeUsers: Math.floor(Math.random() * 500) + 100
    }))
  };
}

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    service: 'Mock HTTP Server'
  });
});

// Dashboard API endpoints
app.get('/admin/dashboard/stats', (req, res) => {
  res.json(generateDashboardStats());
});

app.get('/admin/system/health', (req, res) => {
  res.json({
    status: 'healthy',
    uptime: Math.floor(Math.random() * 100000),
    memoryUsage: Math.floor(Math.random() * 100),
    cpuUsage: Math.floor(Math.random() * 100),
    diskUsage: Math.floor(Math.random() * 100),
    lastChecked: new Date().toISOString()
  });
});

app.get('/api/dashboard/overview', (req, res) => {
  res.json({
    stats: generateDashboardStats(),
    recentTransactions: generateTransactionHistory().slice(0, 5),
    systemAlerts: [
      { type: 'info', message: 'System backup completed', timestamp: new Date().toISOString() },
      { type: 'warning', message: 'High memory usage detected', timestamp: new Date(Date.now() - 60000).toISOString() }
    ]
  });
});

// User management endpoints
app.get('/admin/system/admins', (req, res) => {
  const users = generateUserList();
  const { page = 1, limit = 10, role, status } = req.query;
  
  let filtered = users;
  if (role) filtered = filtered.filter(u => u.role === role);
  if (status) filtered = filtered.filter(u => u.status === status);
  
  const startIndex = (page - 1) * limit;
  const endIndex = startIndex + parseInt(limit);
  
  res.json({
    data: filtered.slice(startIndex, endIndex),
    total: filtered.length,
    page: parseInt(page),
    limit: parseInt(limit)
  });
});

app.get('/api/users', (req, res) => {
  const users = generateUserList();
  const { page = 1, limit = 10, role, status } = req.query;
  
  let filtered = users;
  if (role) filtered = filtered.filter(u => u.role === role);
  if (status) filtered = filtered.filter(u => u.status === status);
  
  const startIndex = (page - 1) * limit;
  const endIndex = startIndex + parseInt(limit);
  
  res.json({
    data: filtered.slice(startIndex, endIndex),
    total: filtered.length,
    page: parseInt(page),
    limit: parseInt(limit)
  });
});

app.post('/admin/system/admins', (req, res) => {
  const newUser = {
    id: Date.now(),
    ...req.body,
    createdAt: new Date().toISOString(),
    status: 'active'
  };
  
  res.status(201).json(newUser);
});

app.post('/api/users', (req, res) => {
  const newUser = {
    id: Date.now(),
    ...req.body,
    createdAt: new Date().toISOString(),
    status: 'active'
  };
  
  res.status(201).json(newUser);
});

app.put('/api/users/:id', (req, res) => {
  const { id } = req.params;
  const updatedUser = {
    id: parseInt(id),
    ...req.body,
    updatedAt: new Date().toISOString()
  };
  
  res.json(updatedUser);
});

app.delete('/api/users/:id', (req, res) => {
  const { id } = req.params;
  res.json({ message: `User ${id} deleted successfully` });
});

// Partner management endpoints
app.get('/partners/', (req, res) => {
  const partners = generatePartnerList();
  const { page = 1, size = 10, status, type } = req.query;
  
  let filtered = partners;
  if (status) filtered = filtered.filter(p => p.status === status);
  if (type) filtered = filtered.filter(p => p.type === type);
  
  const startIndex = (page - 1) * size;
  const endIndex = startIndex + parseInt(size);
  
  res.json({
    data: filtered.slice(startIndex, endIndex),
    total: filtered.length,
    page: parseInt(page),
    size: parseInt(size)
  });
});

app.get('/api/partners', (req, res) => {
  const partners = generatePartnerList();
  const { page = 1, limit = 10, status, type } = req.query;
  
  let filtered = partners;
  if (status) filtered = filtered.filter(p => p.status === status);
  if (type) filtered = filtered.filter(p => p.type === type);
  
  const startIndex = (page - 1) * limit;
  const endIndex = startIndex + parseInt(limit);
  
  res.json({
    data: filtered.slice(startIndex, endIndex),
    total: filtered.length,
    page: parseInt(page),
    limit: parseInt(limit)
  });
});

app.post('/admin/partners', (req, res) => {
  const newPartner = {
    id: Date.now(),
    ...req.body,
    onboardedAt: new Date().toISOString(),
    status: 'pending'
  };
  
  res.status(201).json(newPartner);
});

app.post('/api/partners', (req, res) => {
  const newPartner = {
    id: Date.now(),
    ...req.body,
    onboardedAt: new Date().toISOString(),
    status: 'pending'
  };
  
  res.status(201).json(newPartner);
});

// Transaction endpoints
app.get('/api/transactions', (req, res) => {
  const transactions = generateTransactionHistory();
  const { page = 1, limit = 20, type, status } = req.query;
  
  let filtered = transactions;
  if (type) filtered = filtered.filter(t => t.type === type);
  if (status) filtered = filtered.filter(t => t.status === status);
  
  const startIndex = (page - 1) * limit;
  const endIndex = startIndex + parseInt(limit);
  
  res.json({
    data: filtered.slice(startIndex, endIndex),
    total: filtered.length,
    page: parseInt(page),
    limit: parseInt(limit)
  });
});

// Analytics endpoints
app.get('/api/analytics', (req, res) => {
  res.json(generateAnalyticsData());
});

app.get('/api/analytics/summary', (req, res) => {
  const data = generateAnalyticsData();
  const today = data.daily[data.daily.length - 1];
  const yesterday = data.daily[data.daily.length - 2];
  
  res.json({
    today: today,
    changes: {
      transactions: ((today.transactions - yesterday.transactions) / yesterday.transactions * 100).toFixed(1),
      revenue: ((today.revenue - yesterday.revenue) / yesterday.revenue * 100).toFixed(1),
      activeUsers: ((today.activeUsers - yesterday.activeUsers) / yesterday.activeUsers * 100).toFixed(1)
    }
  });
});

// Energy market endpoints
app.get('/api/energy/market', (req, res) => {
  res.json({
    currentPrice: Math.floor(Math.random() * 50) + 100,
    priceChange: (Math.random() - 0.5) * 10,
    volume24h: Math.floor(Math.random() * 100000) + 50000,
    marketCap: Math.floor(Math.random() * 1000000) + 500000,
    trends: Array.from({ length: 24 }, (_, i) => ({
      hour: i,
      price: Math.floor(Math.random() * 50) + 100,
      volume: Math.floor(Math.random() * 10000) + 1000
    }))
  });
});

// Settings endpoints
app.get('/api/settings', (req, res) => {
  res.json({
    notifications: {
      email: true,
      push: false,
      sms: true
    },
    security: {
      twoFactorAuth: true,
      sessionTimeout: 30,
      ipWhitelist: ['192.168.1.0/24']
    },
    preferences: {
      language: 'ko',
      timezone: 'Asia/Seoul',
      theme: 'light'
    }
  });
});

app.put('/api/settings', (req, res) => {
  res.json({
    ...req.body,
    updatedAt: new Date().toISOString()
  });
});

// Auth endpoints
app.post('/auth/login', (req, res) => {
  const { email, password } = req.body;
  
  // Mock authentication - accept any credentials
  if (email && password) {
    res.json({
      success: true,
      token: 'mock-jwt-token-' + Date.now(),
      user: {
        id: 1,
        email: email,
        name: 'Mock Admin',
        role: 'super-admin',
        permissions: ['read', 'write', 'admin']
      }
    });
  } else {
    res.status(401).json({
      error: 'Unauthorized',
      message: 'Invalid credentials'
    });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('❌ API Error:', err);
  res.status(500).json({
    error: 'Internal Server Error',
    message: err.message,
    timestamp: new Date().toISOString()
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Endpoint ${req.method} ${req.originalUrl} not found`,
    timestamp: new Date().toISOString()
  });
});

const PORT = process.env.PORT || 3001;

const server = app.listen(PORT, () => {
  console.log(`🚀 Mock HTTP Server running on port ${PORT}`);
  console.log(`   Health check: http://localhost:${PORT}/health`);
  console.log(`   Dashboard API: http://localhost:${PORT}/api/dashboard/stats`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('🛑 Mock HTTP Server shutting down...');
  server.close(() => {
    console.log('✅ Mock HTTP Server stopped');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('\n🛑 Mock HTTP Server shutting down...');
  server.close(() => {
    console.log('✅ Mock HTTP Server stopped');
    process.exit(0);
  });
});

module.exports = app;
