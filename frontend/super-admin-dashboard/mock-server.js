const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 8001;

// Middleware
app.use(cors());
app.use(express.json());

// Mock data
const mockPartners = [
  {
    id: 1,
    name: "TechCorp Solutions",
    domain: "techcorp.com", 
    status: "active",
    created_at: "2024-01-15T10:30:00Z",
    total_transactions: 1250,
    total_volume: 85000.50,
    fee_rate: 0.025
  },
  {
    id: 2,
    name: "Global Finance Ltd",
    domain: "globalfinance.io",
    status: "active", 
    created_at: "2024-02-01T14:20:00Z",
    total_transactions: 890,
    total_volume: 125000.75,
    fee_rate: 0.03
  }
];

const mockDashboardStats = {
  total_partners: 5,
  active_partners: 4,
  total_users: 150,
  active_users: 120,
  total_revenue: 75000.0,
  total_transactions_today: 25,
  daily_volume: 125000.0,
  total_energy: 1500000,
  available_energy: 1150000,
  active_wallets: 45
};

const mockSystemHealth = {
  status: "healthy",
  uptime: "99.9%",
  last_check: "2024-07-18T10:30:00Z"
};

// Routes
app.get('/api/v1/test', (req, res) => {
  res.json({ message: "API v1 is working", status: "success" });
});

// Auth endpoints
app.post('/api/v1/auth/login', (req, res) => {
  const { email, password } = req.body;
  
  if (email === 'superadmin@dantaro.com' && password === 'SuperAdmin123!') {
    res.json({
      access_token: 'mock-jwt-token-12345',
      token_type: 'bearer',
      user: {
        id: 1,
        email: 'superadmin@dantaro.com',
        role: 'super_admin'
      }
    });
  } else {
    res.status(401).json({ message: 'Invalid credentials' });
  }
});

// Dashboard endpoints
app.get('/api/v1/admin/dashboard/stats', (req, res) => {
  res.json(mockDashboardStats);
});

app.get('/api/v1/admin/system/health', (req, res) => {
  res.json(mockSystemHealth);
});

// Partners endpoints  
app.get('/api/v1/admin/partners', (req, res) => {
  const page = parseInt(req.query.page) || 1;
  const size = parseInt(req.query.size) || 20;
  
  res.json({
    items: mockPartners,
    total: mockPartners.length,
    page,
    size,
    pages: 1
  });
});

app.get('/api/v1/partners', (req, res) => {
  res.json({
    items: mockPartners,
    total: mockPartners.length,
    page: 1,
    size: 20,
    pages: 1
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Mock API server running on http://localhost:${PORT}`);
  console.log(`Test endpoint: http://localhost:${PORT}/api/v1/test`);
});
