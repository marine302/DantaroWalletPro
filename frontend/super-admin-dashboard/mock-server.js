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

// Audit & Compliance APIs - 백엔드 호환성
app.get('/audit-compliance/logs', (req, res) => {
  const logs = Array.from({ length: 20 }, (_, i) => ({
    id: i + 1,
    user_id: Math.floor(Math.random() * 100) + 1,
    action: ['login', 'transfer', 'withdrawal', 'deposit', 'profile_update'][Math.floor(Math.random() * 5)],
    resource: ['user', 'transaction', 'partner', 'system'][Math.floor(Math.random() * 4)],
    ip_address: `192.168.1.${Math.floor(Math.random() * 255)}`,
    user_agent: 'Mozilla/5.0 (compatible)',
    timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
    risk_level: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)],
    compliance_status: ['compliant', 'flagged', 'under_review'][Math.floor(Math.random() * 3)]
  }));

  // 백엔드 API 응답 형태
  res.json({
    success: true,
    data: {
      items: logs,
      total: 200,
      page: 1,
      size: 20
    }
  });
});

app.post('/audit-compliance/kyc-check', (req, res) => {
  // 백엔드 API 응답 형태
  res.json({
    success: true,
    data: {
      check_id: `kyc_${Date.now()}`,
      user_id: req.body.user_id || 1,
      status: Math.random() > 0.2 ? 'passed' : 'failed',
      risk_score: Math.floor(Math.random() * 100),
      flagged_items: Math.random() > 0.8 ? ['document_verification', 'address_verification'] : [],
      created_at: new Date().toISOString()
    }
  });
});

app.post('/audit-compliance/aml-check', (req, res) => {
  // 백엔드 API 응답 형태
  res.json({
    success: true,
    data: {
      check_id: `aml_${Date.now()}`,
      transaction_id: req.body.transaction_id || `tx_${Date.now()}`,
      status: Math.random() > 0.1 ? 'passed' : 'flagged',
      risk_score: Math.floor(Math.random() * 100),
      flagged_patterns: Math.random() > 0.9 ? ['unusual_amount', 'frequent_transactions'] : [],
      created_at: new Date().toISOString()
    }
  });
});

// Authentication endpoints
app.post('/auth/login', (req, res) => {
  const { email, password } = req.body;
  
  // 간단한 인증 로직
  if (email === 'admin@dantaro.com' && password === 'admin123') {
    res.json({
      access_token: 'mock-jwt-token-12345',
      refresh_token: 'mock-refresh-token-67890',
      token_type: 'bearer',
      expires_in: 3600
    });
  } else {
    res.status(401).json({
      error: 'AUTH_ERROR',
      message: '이메일 또는 비밀번호가 올바르지 않습니다'
    });
  }
});

// 슈퍼 어드민 로그인 엔드포인트 (백엔드 호환성)
app.post('/auth/super-admin/login', (req, res) => {
  const { email, password } = req.body;
  
  // 백엔드 API 응답 형태로 변환
  if (email === 'admin@dantaro.com' && password === 'admin123') {
    res.json({
      access_token: 'mock-super-admin-jwt-token-12345',
      refresh_token: 'mock-super-admin-refresh-token-67890',
      token_type: 'bearer',
      expires_in: 1800
    });
  } else {
    res.status(401).json({
      error: 'AUTH_ERROR',
      message: '이메일 또는 비밀번호가 올바르지 않습니다',
      details: null,
      request_id: Date.now().toString()
    });
  }
});

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

// 백엔드 API 호환성을 위한 /admin/dashboard/overview 엔드포인트
app.get('/admin/dashboard/overview', (req, res) => {
  const stats = generateDashboardStats();
  // 백엔드 API 응답 형태로 변환: { success: true, data: {...} }
  res.json({
    success: true,
    data: {
      total_users: stats.active_wallets || 89,
      total_partners: stats.total_partners || 3,
      total_wallets: stats.active_wallets || 0,
      recent_transactions: stats.total_transactions_today || 0,
      recent_volume: stats.daily_volume || 0.0,
      system_status: "operational",
      last_updated: new Date().toISOString()
    }
  });
});

// 추가: /api/dashboard/stats 엔드포인트
app.get('/api/dashboard/stats', (req, res) => {
  res.json(generateDashboardStats());
});

// System Admins API - 백엔드 호환성
app.get('/admin/system/admins', (req, res) => {
  const admins = generateUserList().filter(user => 
    ['super-admin', 'admin'].includes(user.role)
  ).map(user => ({
    id: user.id,
    username: user.name.toLowerCase().replace(/\s+/g, '_'),
    email: user.email,
    full_name: user.name,
    role: user.role === 'super-admin' ? 'super_admin' : 'admin',
    is_active: user.status === 'active',
    created_at: user.createdAt,
    last_login: user.lastLogin
  }));

  // 백엔드 API 응답 형태
  res.json({
    success: true,
    data: admins
  });
});

// System Health API - 백엔드 호환성  
app.get('/admin/system/health', (req, res) => {
  // 백엔드 API 응답 형태
  res.json({
    success: true,
    data: {
      status: 'healthy',
      database_status: 'connected',
      tron_network_status: 'connected',
      last_check: new Date().toISOString(),
      uptime: Math.floor(Math.random() * 100000),
      errors_count: 0,
      response_time: '15ms'
    }
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

// System Admins PUT/DELETE endpoints (누락된 부분 추가)
app.put('/admin/system/admins/:id', (req, res) => {
  const { id } = req.params;
  const updatedAdmin = {
    id: parseInt(id),
    ...req.body,
    updatedAt: new Date().toISOString()
  };
  
  res.json(updatedAdmin);
});

app.delete('/admin/system/admins/:id', (req, res) => {
  const { id } = req.params;
  res.json({ 
    success: true,
    message: `System admin ${id} deleted successfully` 
  });
});

// Energy Management APIs - 백엔드 호환성
app.get('/admin/energy/pool', (req, res) => {
  // 백엔드 API 응답 형태
  res.json({
    success: true,
    data: {
      id: 1,
      total_energy: 1000000,
      available_energy: 750000,
      reserved_energy: 150000,
      tron_balance: 50000.0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
  });
});

app.get('/admin/energy/status', (req, res) => {
  // 백엔드 API 응답 형태
  res.json({
    success: true,
    data: {
      total_energy: 1000000,
      used_energy: 250000,
      available_energy: 750000,
      active_pools: 3,
      total_partners: 15,
      energy_utilization_rate: 0.25,
      critical_pools: 0,
      warning_pools: 1
    }
  });
});

app.get('/admin/energy/transactions', (req, res) => {
  const transactions = Array.from({ length: 10 }, (_, i) => ({
    id: i + 1,
    partner_id: Math.floor(Math.random() * 5) + 1,
    amount: Math.floor(Math.random() * 10000) + 1000,
    type: Math.random() > 0.5 ? 'allocation' : 'consumption',
    status: ['completed', 'pending', 'failed'][Math.floor(Math.random() * 3)],
    created_at: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString()
  }));

  // 백엔드 API 응답 형태
  res.json({
    success: true,
    data: {
      items: transactions,
      total: 50,
      page: 1,
      size: 10
    }
  });
});

// Fee Management APIs - 백엔드 호환성
app.get('/admin/fees/configs', (req, res) => {
  const configs = Array.from({ length: 5 }, (_, i) => ({
    id: i + 1,
    partner_id: i + 1,
    fee_percentage: (Math.random() * 0.5 + 0.1).toFixed(3),
    min_withdrawal_amount: 100,
    max_withdrawal_amount: 100000,
    daily_withdrawal_limit: 50000,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }));

  // 백엔드 API 응답 형태
  res.json({
    success: true,
    data: configs
  });
});

app.get('/admin/fees/revenue', (req, res) => {
  const revenue = Array.from({ length: 10 }, (_, i) => ({
    id: i + 1,
    partner_id: Math.floor(Math.random() * 5) + 1,
    transaction_id: `tx_${Date.now()}_${i}`,
    fee_amount: (Math.random() * 100).toFixed(2),
    revenue_share: (Math.random() * 50).toFixed(2),
    date: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString()
  }));

  // 백엔드 API 응답 형태
  res.json({
    success: true,
    data: {
      items: revenue,
      total: 100,
      page: 1,
      size: 10
    }
  });
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
  
  // 백엔드 API 호환성을 위한 응답 형태
  res.json({
    success: true,
    data: {
      items: filtered.slice(startIndex, endIndex),
      total: filtered.length,
      page: parseInt(page),
      size: parseInt(size)
    }
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
    // 백엔드 Token 스키마와 정확히 일치하는 응답
    res.json({
      access_token: 'mock-jwt-token-' + Date.now(),
      refresh_token: 'mock-refresh-token-' + Date.now(),
      token_type: 'bearer',
      expires_in: 3600
    });
  } else {
    res.status(401).json({
      error: 'Unauthorized',
      message: 'Invalid credentials'
    });
  }
});

// === External Energy API endpoints (백엔드 스키마와 동일한 구조) ===

function generateExternalEnergyProviders() {
  const providers = [
    {
      id: "tronnrg",
      name: "TronNRG",
      status: "online",
      pricePerEnergy: 0.000012,
      availableEnergy: 500000,
      reliability: 0.98,
      avgResponseTime: 250.5,
      minOrderSize: 1000,
      maxOrderSize: 100000,
      fees: {
        tradingFee: 0.002,
        withdrawalFee: 0.001
      },
      lastUpdated: new Date().toISOString()
    },
    {
      id: "energytron",
      name: "EnergyTron",
      status: "online",
      pricePerEnergy: 0.000015,
      availableEnergy: 350000,
      reliability: 0.95,
      avgResponseTime: 180.3,
      minOrderSize: 500,
      maxOrderSize: 75000,
      fees: {
        tradingFee: 0.0015,
        withdrawalFee: 0.0012
      },
      lastUpdated: new Date().toISOString()
    },
    {
      id: "sunio",
      name: "SUN.io Energy",
      status: "maintenance",
      pricePerEnergy: 0.000018,
      availableEnergy: 200000,
      reliability: 0.92,
      avgResponseTime: 320.7,
      minOrderSize: 2000,
      maxOrderSize: 50000,
      fees: {
        tradingFee: 0.0025,
        withdrawalFee: 0.002
      },
      lastUpdated: new Date().toISOString()
    }
  ];
  
  return providers;
}

function generateMarketSummary() {
  const providers = generateExternalEnergyProviders();
  const onlineProviders = providers.filter(p => p.status === 'online');
  const prices = onlineProviders.map(p => p.pricePerEnergy);
  
  return {
    bestPrice: Math.min(...prices),
    bestProvider: onlineProviders.find(p => p.pricePerEnergy === Math.min(...prices))?.name || "Unknown",
    totalProviders: providers.length,
    activeProviders: onlineProviders.length,
    avgPrice: prices.reduce((a, b) => a + b, 0) / prices.length,
    priceChange24h: (Math.random() - 0.5) * 0.1, // -5% ~ +5%
    totalVolume: Math.floor(Math.random() * 1000000) + 500000,
    lastUpdated: new Date().toISOString()
  };
}

// External Energy API endpoints - 백엔드와 정확히 동일한 구조
app.get('/api/v1/external-energy/providers', (req, res) => {
  const providers = generateExternalEnergyProviders();
  
  // 백엔드와 동일한 응답 구조
  res.json({
    success: true,
    data: providers
  });
});

app.get('/api/v1/external-energy/providers/health', (req, res) => {
  const providers = generateExternalEnergyProviders();
  const healthData = providers.map(provider => ({
    providerId: provider.id,
    status: provider.status,
    lastCheck: new Date().toISOString(),
    responseTime: provider.avgResponseTime,
    uptime: Math.random() * 100
  }));
  
  res.json({
    success: true,
    data: healthData
  });
});

app.get('/api/v1/external-energy/providers/:providerId', (req, res) => {
  const { providerId } = req.params;
  const providers = generateExternalEnergyProviders();
  const provider = providers.find(p => p.id === providerId);
  
  if (!provider) {
    return res.status(404).json({
      success: false,
      error: "Provider not found",
      message: "공급자를 찾을 수 없습니다"
    });
  }
  
  res.json({
    success: true,
    data: provider
  });
});

app.get('/api/v1/external-energy/providers/:providerId/prices', (req, res) => {
  const { providerId } = req.params;
  const providers = generateExternalEnergyProviders();
  const provider = providers.find(p => p.id === providerId);
  
  if (!provider) {
    return res.status(404).json({
      success: false,
      error: "Provider not found"
    });
  }
  
  res.json({
    success: true,
    data: {
      providerId: provider.id,
      currentPrice: provider.pricePerEnergy,
      priceHistory: Array.from({ length: 24 }, (_, i) => ({
        timestamp: new Date(Date.now() - (23 - i) * 60 * 60 * 1000).toISOString(),
        price: provider.pricePerEnergy + (Math.random() - 0.5) * 0.000005
      })),
      lastUpdated: provider.lastUpdated
    }
  });
});

app.get('/api/v1/external-energy/providers/:providerId/balance', (req, res) => {
  const { providerId } = req.params;
  const { address } = req.query;
  
  if (!address) {
    return res.status(400).json({
      success: false,
      error: "Address parameter required"
    });
  }
  
  res.json({
    success: true,
    data: {
      providerId,
      address,
      balance: Math.floor(Math.random() * 10000) + 1000,
      lastUpdated: new Date().toISOString()
    }
  });
});

app.post('/api/v1/external-energy/purchase/multi-provider', (req, res) => {
  const { providers, totalAmount, maxPrice } = req.body;
  
  const orderId = `order_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  res.json({
    success: true,
    data: {
      id: orderId,
      userId: "mock_user",
      totalAmount,
      maxPrice,
      providers: providers.map((p, index) => ({
        providerId: p.providerId,
        amount: p.amount,
        price: 0.000012 + (index * 0.000001),
        status: "pending"
      })),
      status: "pending",
      totalCost: totalAmount * 0.000012,
      createdAt: new Date().toISOString(),
      estimatedCompletion: new Date(Date.now() + 5 * 60 * 1000).toISOString()
    }
  });
});

app.get('/public/providers', (req, res) => {
  const providers = generateExternalEnergyProviders()
    .filter(p => p.status === 'online')
    .map(p => ({
      id: p.id,
      name: p.name,
      pricePerEnergy: p.pricePerEnergy,
      availability: p.availableEnergy > 10000 ? 'high' : 'low'
    }));
  
  res.json({
    success: true,
    data: providers
  });
});

app.get('/public/providers/summary', (req, res) => {
  const summary = generateMarketSummary();
  
  res.json({
    success: true,
    data: summary
  });
});

// === Energy Management API endpoints ===

function generateEnergyPool() {
  return {
    id: 1,
    total_energy: 1000000,
    available_energy: 750000,
    reserved_energy: 150000,
    tron_balance: 5000.0,
    energy_price: 0.00002,
    last_updated: new Date().toISOString(),
    status: 'healthy'
  };
}

function generateEnergyTransaction() {
  const types = ['recharge', 'allocation', 'usage', 'refund'];
  const statuses = ['completed', 'pending', 'failed'];
  
  return {
    id: Math.floor(Math.random() * 1000000),
    type: types[Math.floor(Math.random() * types.length)],
    partner_id: Math.floor(Math.random() * 10) + 1,
    amount: Math.floor(Math.random() * 10000) + 1000,
    tron_cost: Math.random() * 100 + 10,
    status: statuses[Math.floor(Math.random() * statuses.length)],
    transaction_hash: `0x${Math.random().toString(16).substr(2, 64)}`,
    created_at: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
    completed_at: new Date().toISOString()
  };
}

// Energy Pool endpoints
app.get('/admin/energy/pool', (req, res) => {
  const pool = generateEnergyPool();
  res.json(pool);
});

app.post('/admin/energy/recharge', (req, res) => {
  const { amount } = req.body;
  
  if (!amount || amount <= 0) {
    return res.status(400).json({
      error: 'Invalid amount',
      message: 'Amount must be greater than 0'
    });
  }
  
  const transaction = {
    ...generateEnergyTransaction(),
    type: 'recharge',
    amount: amount,
    status: 'completed'
  };
  
  res.json(transaction);
});

app.post('/admin/energy/allocate', (req, res) => {
  const { partner_id, amount } = req.body;
  
  if (!partner_id || !amount || amount <= 0) {
    return res.status(400).json({
      error: 'Invalid parameters',
      message: 'partner_id and positive amount are required'
    });
  }
  
  const transaction = {
    ...generateEnergyTransaction(),
    type: 'allocation',
    partner_id: partner_id,
    amount: amount,
    status: 'completed'
  };
  
  res.json(transaction);
});

app.get('/admin/energy/transactions', (req, res) => {
  const { page = 1, size = 20 } = req.query;
  const pageNum = parseInt(page);
  const sizeNum = parseInt(size);
  
  const transactions = Array.from({ length: 50 }, () => generateEnergyTransaction());
  
  const startIndex = (pageNum - 1) * sizeNum;
  const endIndex = startIndex + sizeNum;
  const paginatedData = transactions.slice(startIndex, endIndex);
  
  res.json({
    data: paginatedData,
    total: transactions.length,
    page: pageNum,
    size: sizeNum,
    pages: Math.ceil(transactions.length / sizeNum)
  });
});

// === Fee Management API endpoints ===

function generateFeeConfig() {
  const feeTypes = ['withdrawal', 'transaction', 'energy_allocation'];
  
  return {
    id: Math.floor(Math.random() * 100) + 1,
    fee_type: feeTypes[Math.floor(Math.random() * feeTypes.length)],
    percentage: Math.random() * 5 + 0.1, // 0.1% ~ 5.1%
    fixed_amount: Math.random() * 10,
    min_fee: Math.random() * 1,
    max_fee: Math.random() * 100 + 50,
    is_active: Math.random() > 0.2,
    created_at: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date().toISOString()
  };
}

function generateFeeRevenue() {
  return {
    id: Math.floor(Math.random() * 1000000),
    partner_id: Math.floor(Math.random() * 10) + 1,
    partner_name: `Partner ${Math.floor(Math.random() * 10) + 1}`,
    fee_type: 'transaction',
    amount: Math.random() * 1000 + 10,
    transaction_count: Math.floor(Math.random() * 100) + 1,
    collected_at: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString()
  };
}

// Fee Management endpoints
app.get('/admin/fees/configs', (req, res) => {
  const configs = Array.from({ length: 10 }, () => generateFeeConfig());
  res.json(configs);
});

app.post('/admin/fees/configs', (req, res) => {
  const newConfig = {
    id: Date.now(),
    ...req.body,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_active: true
  };
  
  res.status(201).json(newConfig);
});

app.put('/admin/fees/configs/:id', (req, res) => {
  const { id } = req.params;
  
  const updatedConfig = {
    id: parseInt(id),
    ...req.body,
    updated_at: new Date().toISOString()
  };
  
  res.json(updatedConfig);
});

app.delete('/admin/fees/configs/:id', (req, res) => {
  const { id } = req.params;
  
  res.json({
    success: true,
    message: `Fee config ${id} deleted successfully`
  });
});

app.get('/admin/fees/revenue', (req, res) => {
  const { page = 1, size = 20, partner_id } = req.query;
  const pageNum = parseInt(page);
  const sizeNum = parseInt(size);
  
  let revenues = Array.from({ length: 100 }, () => generateFeeRevenue());
  
  // Partner ID 필터링
  if (partner_id) {
    revenues = revenues.filter(r => r.partner_id === parseInt(partner_id));
  }
  
  const startIndex = (pageNum - 1) * sizeNum;
  const endIndex = startIndex + sizeNum;
  const paginatedData = revenues.slice(startIndex, endIndex);
  
  res.json({
    data: paginatedData,
    total: revenues.length,
    page: pageNum,
    size: sizeNum,
    pages: Math.ceil(revenues.length / sizeNum)
  });
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

// Partner Energy Management APIs
function generatePartnerEnergyAllocation() {
  const tiers = ['STARTUP', 'BUSINESS', 'ENTERPRISE'];
  const statuses = ['ACTIVE', 'SUSPENDED', 'EXPIRED', 'CANCELLED'];
  const billingCycles = ['DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY'];
  
  const allocatedAmount = Math.floor(Math.random() * 20000000) + 1000000; // 100만 ~ 2100만
  const usedAmount = Math.floor(allocatedAmount * Math.random());
  const purchasePrice = 0.00001; // 0.00001 TRX/Energy
  const markupPercentage = Math.random() * 40 + 10; // 10% ~ 50%
  const rentalPrice = purchasePrice * (1 + markupPercentage / 100);
  
  return {
    id: Math.floor(Math.random() * 1000) + 1,
    partner_id: `partner_${Math.floor(Math.random() * 100) + 1}`,
    partner_name: `파트너 회사 ${Math.floor(Math.random() * 100) + 1}`,
    partner_tier: tiers[Math.floor(Math.random() * tiers.length)],
    allocated_amount: allocatedAmount,
    remaining_amount: allocatedAmount - usedAmount,
    used_amount: usedAmount,
    purchase_price: purchasePrice,
    markup_percentage: markupPercentage,
    rental_price: rentalPrice,
    billing_cycle: billingCycles[Math.floor(Math.random() * billingCycles.length)],
    status: statuses[Math.floor(Math.random() * statuses.length)],
    allocation_date: new Date(Date.now() - Math.random() * 90 * 24 * 60 * 60 * 1000).toISOString(),
    expiry_date: Math.random() > 0.5 ? new Date(Date.now() + Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString() : null,
    last_usage_date: Math.random() > 0.3 ? new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString() : null,
    utilization_rate: allocatedAmount > 0 ? (usedAmount / allocatedAmount) * 100 : 0,
    total_revenue: (rentalPrice - purchasePrice) * usedAmount,
    notes: Math.random() > 0.7 ? '특별 할인 적용' : null,
    created_at: new Date(Date.now() - Math.random() * 100 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - Math.random() * 10 * 24 * 60 * 60 * 1000).toISOString()
  };
}

function generatePartnerEnergyUsage() {
  return {
    id: Math.floor(Math.random() * 10000) + 1,
    allocation_id: Math.floor(Math.random() * 100) + 1,
    partner_id: `partner_${Math.floor(Math.random() * 100) + 1}`,
    used_amount: Math.floor(Math.random() * 100000) + 1000,
    unit_price: 0.0000135, // 렌탈 가격
    total_cost: 0, // 계산됨
    usage_date: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
    transaction_hash: Math.random() > 0.3 ? `0x${Math.random().toString(16).substring(2, 66)}` : null,
    billing_status: ['PENDING', 'BILLED', 'PAID'][Math.floor(Math.random() * 3)],
    description: Math.random() > 0.5 ? `에너지 사용 - ${new Date().toLocaleDateString()}` : null
  };
}

function generateEnergyMarginConfig() {
  const configs = [
    {
      id: 1,
      partner_tier: 'STARTUP',
      default_margin_percentage: 35.0,
      min_margin_percentage: 25.0,
      max_margin_percentage: 50.0,
      volume_threshold_1: 500000,
      volume_margin_1: 5.0,
      volume_threshold_2: 2000000,
      volume_margin_2: 10.0,
      effective_date: new Date().toISOString(),
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    {
      id: 2,
      partner_tier: 'BUSINESS',
      default_margin_percentage: 25.0,
      min_margin_percentage: 15.0,
      max_margin_percentage: 35.0,
      volume_threshold_1: 1000000,
      volume_margin_1: 3.0,
      volume_threshold_2: 5000000,
      volume_margin_2: 7.0,
      effective_date: new Date().toISOString(),
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    {
      id: 3,
      partner_tier: 'ENTERPRISE',
      default_margin_percentage: 15.0,
      min_margin_percentage: 8.0,
      max_margin_percentage: 25.0,
      volume_threshold_1: 10000000,
      volume_margin_1: 2.0,
      volume_threshold_2: 50000000,
      volume_margin_2: 5.0,
      effective_date: new Date().toISOString(),
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
  ];
  
  return configs;
}

// 파트너 에너지 할당
app.post('/partners/:partnerId/energy/allocate', (req, res) => {
  const { partnerId } = req.params;
  const allocation = generatePartnerEnergyAllocation();
  allocation.partner_id = partnerId;
  allocation.partner_name = req.body.partner_name || allocation.partner_name;
  allocation.partner_tier = req.body.partner_tier || allocation.partner_tier;
  allocation.allocated_amount = req.body.allocated_amount || allocation.allocated_amount;
  allocation.purchase_price = req.body.purchase_price || allocation.purchase_price;
  allocation.markup_percentage = req.body.markup_percentage || allocation.markup_percentage;
  allocation.rental_price = allocation.purchase_price * (1 + allocation.markup_percentage / 100);
  
  res.status(201).json(allocation);
});

// 파트너 에너지 할당 목록
app.get('/partners/:partnerId/energy/allocations', (req, res) => {
  const { partnerId } = req.params;
  const { status, skip = 0, limit = 100 } = req.query;
  
  let allocations = Array.from({ length: 10 }, () => generatePartnerEnergyAllocation());
  allocations.forEach(allocation => {
    allocation.partner_id = partnerId;
  });
  
  if (status) {
    allocations = allocations.filter(a => a.status === status);
  }
  
  const startIndex = parseInt(skip);
  const endIndex = startIndex + parseInt(limit);
  const paginatedData = allocations.slice(startIndex, endIndex);
  
  res.json(paginatedData);
});

// 에너지 할당 수정
app.put('/partners/:partnerId/energy/allocations/:allocationId', (req, res) => {
  const { partnerId, allocationId } = req.params;
  const allocation = generatePartnerEnergyAllocation();
  allocation.id = parseInt(allocationId);
  allocation.partner_id = partnerId;
  
  // 업데이트 필드 적용
  Object.keys(req.body).forEach(key => {
    allocation[key] = req.body[key];
  });
  
  // 마진율 변경 시 렌탈 가격 재계산
  if (req.body.markup_percentage) {
    allocation.rental_price = allocation.purchase_price * (1 + allocation.markup_percentage / 100);
  }
  
  allocation.updated_at = new Date().toISOString();
  
  res.json(allocation);
});

// 에너지 사용량 기록
app.post('/partners/:partnerId/energy/usage', (req, res) => {
  const { partnerId } = req.params;
  const usage = generatePartnerEnergyUsage();
  usage.partner_id = partnerId;
  usage.allocation_id = req.body.allocation_id || usage.allocation_id;
  usage.used_amount = req.body.used_amount || usage.used_amount;
  usage.total_cost = usage.used_amount * usage.unit_price;
  usage.transaction_hash = req.body.transaction_hash || usage.transaction_hash;
  usage.description = req.body.description || usage.description;
  
  res.status(201).json(usage);
});

// 파트너 에너지 사용량 조회
app.get('/partners/:partnerId/energy/usage', (req, res) => {
  const { partnerId } = req.params;
  const { allocation_id, start_date, end_date, skip = 0, limit = 100 } = req.query;
  
  let usageRecords = Array.from({ length: 20 }, () => generatePartnerEnergyUsage());
  usageRecords.forEach(usage => {
    usage.partner_id = partnerId;
    usage.total_cost = usage.used_amount * usage.unit_price;
  });
  
  if (allocation_id) {
    usageRecords = usageRecords.filter(u => u.allocation_id === parseInt(allocation_id));
  }
  
  if (start_date) {
    usageRecords = usageRecords.filter(u => new Date(u.usage_date) >= new Date(start_date));
  }
  
  if (end_date) {
    usageRecords = usageRecords.filter(u => new Date(u.usage_date) <= new Date(end_date));
  }
  
  const startIndex = parseInt(skip);
  const endIndex = startIndex + parseInt(limit);
  const paginatedData = usageRecords.slice(startIndex, endIndex);
  
  res.json(paginatedData);
});

// 에너지 수익 분석
app.get('/admin/energy/revenue-analytics', (req, res) => {
  const allocations = Array.from({ length: 50 }, () => generatePartnerEnergyAllocation());
  
  const totalRevenue = allocations.reduce((sum, a) => sum + a.total_revenue, 0);
  const totalUsage = allocations.reduce((sum, a) => sum + a.used_amount, 0);
  const partnerCount = new Set(allocations.map(a => a.partner_id)).size;
  const avgMarginRate = allocations.reduce((sum, a) => sum + a.markup_percentage, 0) / allocations.length;
  
  // 파트너별 수익
  const partnerRevenue = {};
  allocations.forEach(allocation => {
    if (!partnerRevenue[allocation.partner_id]) {
      partnerRevenue[allocation.partner_id] = {
        partner_name: allocation.partner_name,
        revenue: 0,
        usage: 0
      };
    }
    partnerRevenue[allocation.partner_id].revenue += allocation.total_revenue;
    partnerRevenue[allocation.partner_id].usage += allocation.used_amount;
  });
  
  const topPartners = Object.entries(partnerRevenue)
    .map(([partner_id, data]) => ({ partner_id, ...data }))
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, 10);
  
  // 등급별 수익
  const revenueByTier = {};
  ['STARTUP', 'BUSINESS', 'ENTERPRISE'].forEach(tier => {
    revenueByTier[tier] = allocations
      .filter(a => a.partner_tier === tier)
      .reduce((sum, a) => sum + a.total_revenue, 0);
  });
  
  res.json({
    total_revenue: totalRevenue,
    total_margin: totalRevenue, // 실제로는 총 마진만 계산
    total_usage: totalUsage,
    partner_count: partnerCount,
    avg_margin_rate: avgMarginRate,
    top_partners: topPartners,
    revenue_by_tier: revenueByTier,
    monthly_trend: [] // TODO: 구현 필요
  });
});

// 마진 설정 조회
app.get('/admin/energy/margin-config', (req, res) => {
  const configs = generateEnergyMarginConfig();
  res.json(configs);
});

// 마진 설정 생성/수정
app.post('/admin/energy/margin-config', (req, res) => {
  const newConfig = {
    id: Date.now(),
    ...req.body,
    effective_date: new Date().toISOString(),
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
  
  res.status(201).json(newConfig);
});

// ...existing code...
