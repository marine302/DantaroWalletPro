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
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private data: Partial<RealtimeData> = {};
  private isConnecting: boolean = false;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectInterval: number = 3000;

  private constructor() {
    this.wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3002';
    this.connect();
  }

  static getInstance(): RealtimeManager {
    if (!RealtimeManager.instance) {
      RealtimeManager.instance = new RealtimeManager();
    }
    return RealtimeManager.instance;
  }

  private connect() {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.isConnecting = true;

    try {
      this.ws = new WebSocket(this.wsUrl);

      this.ws.onopen = () => {
        console.log('RealtimeManager: WebSocket connected');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const _message = JSON.parse(event.data);
          this.updateData(_message.type, _message.data);
        } catch (error) {
          console.error('RealtimeManager: Failed to parse message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('RealtimeManager: WebSocket disconnected');
        this.isConnecting = false;
        this.ws = null;

        // Auto-reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          setTimeout(() => this.connect(), this.reconnectInterval);
        }
      };

      this.ws.onerror = (error) => {
        console.error('RealtimeManager: WebSocket error:', error);
        this.isConnecting = false;
      };

    } catch (error) {
      console.error('RealtimeManager: Failed to create WebSocket:', error);
      this.isConnecting = false;
    }
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
      const _listeners = this.listeners.get(dataType);
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
    const _listeners = this.listeners.get(dataType);
    if (_listeners) {
      _listeners.forEach(callback => callback(data));
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
