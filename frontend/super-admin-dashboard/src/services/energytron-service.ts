/**
 * EnergyTron API 연동 서비스
 * 백엔드 API와 연동하여 EnergyTron 에너지 거래 데이터를 관리합니다.
 * 백엔드 구현 완료 시까지 Mock 데이터 사용
 */

export interface EnergyTronPrice {
  price: number;
  currency: 'TRX' | 'USDT';
  timestamp: string;
  change24h: number;
  volume24h: number;
}

export interface EnergyTronMarketData {
  currentPrice: number;
  bestBuyPrice: number;
  bestSellPrice: number;
  dailyVolume: number;
  dailyChange: number;
  availableEnergy: number;
  timestamp: string;
  priceHistory24h: Array<{
    time: string;
    price: number;
  }>;
}

export interface EnergyTronProvider {
  id: string;
  name: string;
  status: 'online' | 'offline' | 'maintenance';
  pricePerEnergy: number;
  availableEnergy: number;
  reliability: number;
  avgResponseTime: number;
  minOrderSize: number;
  maxOrderSize: number;
  fees: {
    tradingFee: number;
    withdrawalFee: number;
  };
  supportedCurrencies: string[];
  lastUpdated: string;
}

export interface EnergyTronOrderRequest {
  amount: number;
  priceLimit?: number;
  orderType: 'market' | 'limit';
  duration: number; // 에너지 임대 기간 (일)
  currency: 'TRX' | 'USDT';
}

export interface EnergyTronOrderResponse {
  orderId: string;
  status: 'pending' | 'filled' | 'cancelled' | 'failed';
  amount: number;
  price: number;
  totalCost: number;
  currency: string;
  estimatedFillTime?: string;
  createdAt: string;
  updatedAt: string;
}

export interface EnergyTronTransaction {
  id: string;
  orderId: string;
  amount: number;
  price: number;
  totalCost: number;
  currency: string;
  status: 'completed' | 'pending' | 'failed';
  energyReceived: number;
  duration: number;
  expiresAt: string;
  createdAt: string;
}

export interface ProviderComparison {
  bestPrice: {
    provider: string;
    price: number;
    savings: number;
  };
  bestReliability: {
    provider: string;
    reliability: number;
  };
  comparison: Array<{
    provider: string;
    avgPrice: number;
    reliability: number;
    responseTime: number;
    availableEnergy: number;
  }>;
  recommendation: {
    suggested: string;
    reason: string;
    savings: string;
  };
}

class EnergyTronService {
  private baseURL: string;
  private useMockData: boolean;

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000/api/v1';
    this.useMockData = process.env.NEXT_PUBLIC_USE_BACKEND_API !== 'true';
  }

  /**
   * EnergyTron 공급자 목록 조회
   */
  async getProviders(): Promise<EnergyTronProvider[]> {
    if (this.useMockData) {
      return this.getMockProviders();
    }

    try {
      const response = await fetch(`${this.baseURL}/external-energy/energytron/providers`);
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.warn('❌ EnergyTron providers API failed, using mock data:', error);
      return this.getMockProviders();
    }
  }

  /**
   * EnergyTron 시장 데이터 조회
   */
  async getMarketData(): Promise<EnergyTronMarketData> {
    if (this.useMockData) {
      return this.getMockMarketData();
    }

    try {
      const response = await fetch(`${this.baseURL}/external-energy/energytron/market/data`);
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.warn('❌ EnergyTron market data API failed, using mock data:', error);
      return this.getMockMarketData();
    }
  }

  /**
   * EnergyTron 주문 생성
   */
  async createOrder(order: EnergyTronOrderRequest): Promise<EnergyTronOrderResponse> {
    if (this.useMockData) {
      return this.createMockOrder(order);
    }

    try {
      const response = await fetch(`${this.baseURL}/external-energy/energytron/orders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(order),
      });
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.warn('❌ EnergyTron create order API failed, using mock data:', error);
      return this.createMockOrder(order);
    }
  }

  /**
   * 공급자 비교 (TronNRG vs EnergyTron)
   */
  async compareProviders(): Promise<ProviderComparison> {
    if (this.useMockData) {
      return this.getMockComparison();
    }

    try {
      const response = await fetch(`${this.baseURL}/external-energy/providers/compare`);
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.warn('❌ Provider comparison API failed, using mock data:', error);
      return this.getMockComparison();
    }
  }

  /**
   * 실시간 가격 WebSocket 연결
   */
  connectPriceStream(onMessage: (data: any) => void): WebSocket | null {
    if (this.useMockData) {
      return this.createMockWebSocket(onMessage);
    }

    try {
      const ws = new WebSocket(`ws://localhost:8000/ws/external-energy/energytron/prices`);
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        onMessage(data);
      };
      return ws;
    } catch (error) {
      console.warn('❌ EnergyTron WebSocket failed, using mock stream:', error);
      return this.createMockWebSocket(onMessage);
    }
  }

  // =========================
  // Mock 데이터 메서드들
  // =========================

  private getMockProviders(): EnergyTronProvider[] {
    return [
      {
        id: 'energytron-pool-1',
        name: 'EnergyTron Pool A',
        status: 'online',
        pricePerEnergy: 0.0039,
        availableEnergy: 2800000,
        reliability: 98.5,
        avgResponseTime: 320,
        minOrderSize: 50000,
        maxOrderSize: 5000000,
        fees: {
          tradingFee: 0.002,
          withdrawalFee: 100,
        },
        supportedCurrencies: ['TRX', 'USDT'],
        lastUpdated: new Date().toISOString(),
      },
      {
        id: 'energytron-pool-2',
        name: 'EnergyTron Pool B',
        status: 'online',
        pricePerEnergy: 0.0041,
        availableEnergy: 1900000,
        reliability: 97.8,
        avgResponseTime: 280,
        minOrderSize: 25000,
        maxOrderSize: 3000000,
        fees: {
          tradingFee: 0.0018,
          withdrawalFee: 80,
        },
        supportedCurrencies: ['TRX', 'USDT'],
        lastUpdated: new Date().toISOString(),
      },
      {
        id: 'energytron-pool-3',
        name: 'EnergyTron Pool C',
        status: 'maintenance',
        pricePerEnergy: 0.0037,
        availableEnergy: 0,
        reliability: 99.1,
        avgResponseTime: 210,
        minOrderSize: 100000,
        maxOrderSize: 8000000,
        fees: {
          tradingFee: 0.0015,
          withdrawalFee: 120,
        },
        supportedCurrencies: ['TRX', 'USDT'],
        lastUpdated: new Date().toISOString(),
      },
    ];
  }

  private getMockMarketData(): EnergyTronMarketData {
    const currentPrice = 0.0039;
    const change = (Math.random() - 0.5) * 0.0005;
    
    return {
      currentPrice: currentPrice + change,
      bestBuyPrice: currentPrice - 0.0001,
      bestSellPrice: currentPrice + 0.0001,
      dailyVolume: 1250000,
      dailyChange: 1.8,
      availableEnergy: 2800000,
      timestamp: new Date().toISOString(),
      priceHistory24h: this.generateMockPriceHistory(currentPrice),
    };
  }

  private generateMockPriceHistory(basePrice: number) {
    const history = [];
    const now = new Date();
    
    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      const variation = (Math.random() - 0.5) * 0.0008;
      history.push({
        time: time.toISOString(),
        price: basePrice + variation,
      });
    }
    
    return history;
  }

  private createMockOrder(order: EnergyTronOrderRequest): EnergyTronOrderResponse {
    const orderId = `ET-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
    const price = order.priceLimit || 0.0039;
    const totalCost = order.amount * price;

    return {
      orderId,
      status: 'pending',
      amount: order.amount,
      price,
      totalCost,
      currency: order.currency,
      estimatedFillTime: new Date(Date.now() + 2 * 60 * 1000).toISOString(), // 2분 후
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  }

  private getMockComparison(): ProviderComparison {
    return {
      bestPrice: {
        provider: 'energytron-pool-1',
        price: 0.0039,
        savings: 0.0002,
      },
      bestReliability: {
        provider: 'tronnrg-pool-a',
        reliability: 99.2,
      },
      comparison: [
        {
          provider: 'TronNRG',
          avgPrice: 0.0041,
          reliability: 99.2,
          responseTime: 280,
          availableEnergy: 1500000,
        },
        {
          provider: 'EnergyTron',
          avgPrice: 0.0039,
          reliability: 98.5,
          responseTime: 320,
          availableEnergy: 2800000,
        },
      ],
      recommendation: {
        suggested: 'energytron-pool-1',
        reason: 'Lower price with acceptable reliability',
        savings: '4.9% cost reduction',
      },
    };
  }

  private createMockWebSocket(onMessage: (data: any) => void): WebSocket | null {
    // Mock WebSocket으로 실시간 가격 업데이트 시뮬레이션
    const interval = setInterval(() => {
      const mockData = {
        type: 'price_update',
        provider: 'energytron',
        data: {
          price: 0.0039 + (Math.random() - 0.5) * 0.0004,
          change: (Math.random() - 0.5) * 0.0002,
          volume: Math.floor(Math.random() * 50000) + 100000,
          timestamp: new Date().toISOString(),
        },
      };
      onMessage(mockData);
    }, 3000); // 3초마다 업데이트

    // Mock WebSocket 객체 반환 (cleanup을 위해)
    return {
      close: () => clearInterval(interval),
      readyState: 1, // OPEN
    } as WebSocket;
  }
}

// 싱글톤 인스턴스 생성
export const energyTronService = new EnergyTronService();
export default energyTronService;
