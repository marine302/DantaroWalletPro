export interface RealtimeData {
  systemStats: {
    cpuUsage: number;
    memoryUsage: number;
    diskUsage: number;
    activeConnections: number;
  };
  dashboardStats: {
    activeUsers: number;
    totalTransactions: number;
    energyTrading: number;
    revenue: number;
  };
  alerts: Array<{
    id: string;
    type: 'error' | 'warning' | 'info';
    message: string;
    timestamp: string;
  }>;
  energyMarket: {
    currentPrice: number;
    priceChange: number;
    volume: number;
    providers: Array<{
      id: string;
      name: string;
      status: 'online' | 'offline';
      price: number;
    }>;
  };
  transactions: Array<{
    id: string;
    type: string;
    amount: number;
    status: 'pending' | 'completed' | 'failed';
    timestamp: string;
  }>;
}

class RealtimeManager {
  private static instance: RealtimeManager;
  private wsUrl: string;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private data: Partial<RealtimeData> = {};

  private constructor() {
    this.wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
  }

  static getInstance(): RealtimeManager {
    if (!RealtimeManager.instance) {
      RealtimeManager.instance = new RealtimeManager();
    }
    return RealtimeManager.instance;
  }

  subscribe(dataType: keyof RealtimeData, callback: (data: any) => void) {
    if (!this.listeners.has(dataType)) {
      this.listeners.set(dataType, new Set());
    }
    this.listeners.get(dataType)!.add(callback);

    // Return current data if available
    if (this.data[dataType]) {
      callback(this.data[dataType]);
    }

    // Return unsubscribe function
    return () => {
      const listeners = this.listeners.get(dataType);
      if (listeners) {
        listeners.delete(callback);
        if (listeners.size === 0) {
          this.listeners.delete(dataType);
        }
      }
    };
  }

  updateData(dataType: keyof RealtimeData, data: any) {
    this.data[dataType] = data;
    
    // Notify all listeners for this data type
    const listeners = this.listeners.get(dataType);
    if (listeners) {
      listeners.forEach(callback => callback(data));
    }
  }

  getData(dataType: keyof RealtimeData) {
    return this.data[dataType];
  }

  getAllData(): Partial<RealtimeData> {
    return { ...this.data };
  }
}

export const realtimeManager = RealtimeManager.getInstance();
