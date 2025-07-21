/**
 * TronNRG API 연동 서비스
 * 실제 TronNRG API와 연동하여 에너지 거래 데이터를 관리합니다.
 */

export interface TronNRGPrice {
  price: number;
  currency: 'TRX' | 'USDT';
  timestamp: string;
  change24h: number;
  volume24h: number;
}

export interface TronNRGMarketData {
  currentPrice: number;
  bestBuyPrice: number;
  bestSellPrice: number;
  dailyVolume: number;
  dailyChange: number;
  availableEnergy: number;
  timestamp: string;
}

export interface TronNRGProvider {
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
  lastUpdated: string;
}

export interface TronNRGOrderRequest {
  amount: number;
  priceLimit?: number;
  orderType: 'market' | 'limit';
  duration: number; // 에너지 임대 기간 (일)
}

export interface TronNRGOrderResponse {
  orderId: string;
  status: 'pending' | 'filled' | 'cancelled' | 'failed';
  amount: number;
  price: number;
  totalCost: number;
  timestamp: string;
  estimatedDelivery: string;
}

export interface TronNRGTransaction {
  id: string;
  type: 'purchase' | 'sale' | 'rental';
  amount: number;
  price: number;
  totalCost: number;
  status: 'completed' | 'pending' | 'failed';
  timestamp: string;
  providerId: string;
  providerName: string;
  transactionHash?: string;
}

class TronNRGService {
  private baseURL: string;
  private apiKey: string;
  private isProduction: boolean;

  constructor() {
    // 환경 변수에서 설정 로드
    this.baseURL = process.env.NEXT_PUBLIC_TRONNRG_API_URL || 'https://api.tronnrg.com/v1';
    this.apiKey = process.env.NEXT_PUBLIC_TRONNRG_API_KEY || 'demo_key';
    this.isProduction = false; // 강제로 개발 모드로 설정
    
    console.log('🔋 TronNRG Service initialized:', {
      baseURL: this.baseURL,
      isProduction: this.isProduction,
      hasApiKey: !!this.apiKey,
      forceMockMode: true
    });
  }

  /**
   * API 요청 헬퍼 메서드
   */
  private async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    // 개발 환경에서는 바로 mock 데이터 반환
    if (!this.isProduction) {
      console.log('🎭 Using mock data for development:', endpoint);
      await new Promise(resolve => setTimeout(resolve, 100)); // 작은 지연 시뮬레이션
      return this.getMockData(endpoint) as T;
    }

    const url = `${this.baseURL}${endpoint}`;
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'X-API-Key': this.apiKey,
      'User-Agent': 'DantaroWallet-SuperAdmin/1.0'
    };

    try {
      console.log(`🌐 TronNRG API Request: ${options.method || 'GET'} ${url}`);
      
      const response = await fetch(url, {
        ...options,
        headers: {
          ...defaultHeaders,
          ...options.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`TronNRG API Error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log(`✅ TronNRG API Response:`, data);
      
      return data;
    } catch (error) {
      console.error('❌ TronNRG API Error:', error);
      
      // 프로덕션이 아닌 경우 Mock 데이터 반환
      if (!this.isProduction) {
        console.log('🎭 Returning mock data for development');
        return this.getMockData(endpoint) as T;
      }
      
      throw error;
    }
  }

  /**
   * 개발용 Mock 데이터 생성
   */
  private getMockData(endpoint: string): any {
    const now = new Date().toISOString();
    
    switch (true) {
      case endpoint.includes('/market/price'):
        return {
          price: 0.0041 + (Math.random() - 0.5) * 0.0001,
          currency: 'TRX',
          timestamp: now,
          change24h: (Math.random() - 0.5) * 10,
          volume24h: Math.floor(Math.random() * 1000000)
        };
        
      case endpoint.includes('/market/data'):
        return {
          currentPrice: 0.0041,
          bestBuyPrice: 0.0040,
          bestSellPrice: 0.0042,
          dailyVolume: 850000,
          dailyChange: 2.5,
          availableEnergy: 15000000,
          timestamp: now
        };
        
      case endpoint.includes('/providers'):
        return [
          {
            id: 'tronnrg-1',
            name: 'TronNRG Pool A',
            status: 'online',
            pricePerEnergy: 0.0041,
            availableEnergy: 5000000,
            reliability: 99.2,
            avgResponseTime: 1.8,
            minOrderSize: 1000,
            maxOrderSize: 10000000,
            fees: { tradingFee: 0.001, withdrawalFee: 0.0005 },
            lastUpdated: now
          },
          {
            id: 'tronnrg-2',
            name: 'TronNRG Pool B',
            status: 'online',
            pricePerEnergy: 0.0042,
            availableEnergy: 3000000,
            reliability: 98.7,
            avgResponseTime: 2.1,
            minOrderSize: 500,
            maxOrderSize: 5000000,
            fees: { tradingFee: 0.0015, withdrawalFee: 0.0003 },
            lastUpdated: now
          }
        ];
        
      case endpoint.includes('/transactions'):
        return [
          {
            id: 'tx_' + Date.now(),
            type: 'purchase',
            amount: 10000,
            price: 0.0041,
            totalCost: 41,
            status: 'completed',
            timestamp: now,
            providerId: 'tronnrg-1',
            providerName: 'TronNRG Pool A',
            transactionHash: '0x' + Math.random().toString(16).substr(2, 8)
          }
        ];
        
      default:
        return { message: 'Mock data not available for this endpoint' };
    }
  }

  /**
   * 현재 에너지 가격 조회
   */
  async getCurrentPrice(): Promise<TronNRGPrice> {
    return this.makeRequest<TronNRGPrice>('/market/price');
  }

  /**
   * 시장 데이터 조회
   */
  async getMarketData(): Promise<TronNRGMarketData> {
    return this.makeRequest<TronNRGMarketData>('/market/data');
  }

  /**
   * 사용 가능한 공급자 목록 조회
   */
  async getProviders(): Promise<TronNRGProvider[]> {
    console.log('🔍 TronNRG getProviders called');
    const result = await this.makeRequest<TronNRGProvider[]>('/providers');
    console.log('📋 TronNRG providers result:', result);
    return result;
  }

  /**
   * 특정 공급자 정보 조회
   */
  async getProvider(providerId: string): Promise<TronNRGProvider> {
    return this.makeRequest<TronNRGProvider>(`/providers/${providerId}`);
  }

  /**
   * 에너지 구매 주문
   */
  async createOrder(orderRequest: TronNRGOrderRequest): Promise<TronNRGOrderResponse> {
    return this.makeRequest<TronNRGOrderResponse>('/orders', {
      method: 'POST',
      body: JSON.stringify(orderRequest),
    });
  }

  /**
   * 주문 상태 조회
   */
  async getOrder(orderId: string): Promise<TronNRGOrderResponse> {
    return this.makeRequest<TronNRGOrderResponse>(`/orders/${orderId}`);
  }

  /**
   * 거래 내역 조회
   */
  async getTransactions(limit: number = 50): Promise<TronNRGTransaction[]> {
    return this.makeRequest<TronNRGTransaction[]>(`/transactions?limit=${limit}`);
  }

  /**
   * 실시간 가격 업데이트를 위한 WebSocket 연결
   */
  connectPriceStream(onUpdate: (price: TronNRGPrice) => void): WebSocket | null {
    if (!this.isProduction) {
      // 개발환경에서는 Mock 데이터로 시뮬레이션
      const interval = setInterval(() => {
        onUpdate(this.getMockData('/market/price') as TronNRGPrice);
      }, 5000);
      
      // cleanup을 위한 fake WebSocket 객체 반환
      return {
        close: () => clearInterval(interval),
        readyState: 1,
      } as any;
    }

    try {
      const ws = new WebSocket(`wss://api.tronnrg.com/v1/stream/price`);
      
      ws.onopen = () => {
        console.log('🔌 TronNRG price stream connected');
        ws.send(JSON.stringify({ type: 'subscribe', channel: 'price' }));
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'price_update') {
            onUpdate(data.data);
          }
        } catch (error) {
          console.error('❌ Error parsing price stream data:', error);
        }
      };
      
      ws.onerror = (error) => {
        console.error('❌ TronNRG WebSocket error:', error);
      };
      
      ws.onclose = () => {
        console.log('🔌 TronNRG price stream disconnected');
      };
      
      return ws;
    } catch (error) {
      console.error('❌ Failed to connect to TronNRG price stream:', error);
      return null;
    }
  }

  /**
   * API 연결 상태 확인
   */
  async checkHealth(): Promise<{ status: 'healthy' | 'unhealthy'; latency: number }> {
    const startTime = Date.now();
    
    try {
      await this.makeRequest('/health');
      const latency = Date.now() - startTime;
      
      return { status: 'healthy', latency };
    } catch (error) {
      const latency = Date.now() - startTime;
      return { status: 'unhealthy', latency };
    }
  }
}

// 싱글톤 인스턴스 생성
export const tronNRGService = new TronNRGService();

export default TronNRGService;
