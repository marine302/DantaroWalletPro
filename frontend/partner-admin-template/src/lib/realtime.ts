/**
 * 실시간 데이터 처리 - WebSocket 및 Server-Sent Events
 */

export interface RealtimeMessage<T = unknown> {
  type: string;
  payload: T;
  timestamp: string;
  id?: string;
}

export interface RealtimeSubscription {
  id: string;
  channel: string;
  callback: (message: RealtimeMessage) => void;
  options?: {
    autoReconnect?: boolean;
    maxReconnectAttempts?: number;
    reconnectInterval?: number;
  };
}

// WebSocket 관리자
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private subscriptions = new Map<string, RealtimeSubscription>();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 3000;
  private isConnecting = false;
  private url: string;

  constructor(url: string = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws') {
    this.url = url;
  }

  // 연결
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
        resolve();
        return;
      }

      this.isConnecting = true;

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: RealtimeMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.isConnecting = false;
          this.handleReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          reject(error);
        };
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  // 연결 해제
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.subscriptions.clear();
  }

  // 메시지 전송
  send(message: Record<string, unknown>) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  // 채널 구독
  subscribe(channel: string, callback: (message: RealtimeMessage) => void, options?: RealtimeSubscription['options']): string {
    const id = `${channel}_${Date.now()}_${Math.random()}`;
    
    this.subscriptions.set(id, {
      id,
      channel,
      callback,
      options
    });

    // 서버에 구독 요청 전송
    this.send({
      type: 'subscribe',
      channel
    });

    return id;
  }

  // 구독 해제
  unsubscribe(subscriptionId: string) {
    const subscription = this.subscriptions.get(subscriptionId);
    if (subscription) {
      this.subscriptions.delete(subscriptionId);
      
      // 같은 채널의 다른 구독이 없으면 서버에 구독 해제 요청
      const hasOtherSubscriptions = Array.from(this.subscriptions.values())
        .some(sub => sub.channel === subscription.channel);
      
      if (!hasOtherSubscriptions) {
        this.send({
          type: 'unsubscribe',
          channel: subscription.channel
        });
      }
    }
  }

  // 메시지 처리
  private handleMessage(message: RealtimeMessage) {
    for (const subscription of this.subscriptions.values()) {
      if (message.type === subscription.channel || message.type === 'broadcast') {
        try {
          subscription.callback(message);
        } catch (error) {
          console.error(`Error in subscription callback for ${subscription.channel}:`, error);
        }
      }
    }
  }

  // 재연결 처리
  private handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    setTimeout(() => {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      this.connect().catch(error => {
        console.error('Reconnection failed:', error);
      });
    }, this.reconnectInterval);
  }

  // 연결 상태 확인
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Server-Sent Events 관리자
export class SSEManager {
  private eventSources = new Map<string, EventSource>();
  private subscriptions = new Map<string, RealtimeSubscription>();

  // SSE 연결
  connect(endpoint: string, channels: string[] = []): Promise<string> {
    return new Promise((resolve, reject) => {
      const url = new URL(endpoint, process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');
      
      if (channels.length > 0) {
        url.searchParams.set('channels', channels.join(','));
      }

      const eventSource = new EventSource(url.toString());
      const connectionId = `sse_${Date.now()}_${Math.random()}`;

      eventSource.onopen = () => {
        console.log('SSE connected:', endpoint);
        resolve(connectionId);
      };

      eventSource.onmessage = (event) => {
        try {
          const message: RealtimeMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse SSE message:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        reject(error);
      };

      this.eventSources.set(connectionId, eventSource);
    });
  }

  // SSE 연결 해제
  disconnect(connectionId: string) {
    const eventSource = this.eventSources.get(connectionId);
    if (eventSource) {
      eventSource.close();
      this.eventSources.delete(connectionId);
    }
  }

  // 모든 SSE 연결 해제
  disconnectAll() {
    for (const [, eventSource] of this.eventSources) {
      eventSource.close();
    }
    this.eventSources.clear();
    this.subscriptions.clear();
  }

  // 채널 구독
  subscribe(channel: string, callback: (message: RealtimeMessage) => void): string {
    const id = `${channel}_${Date.now()}_${Math.random()}`;
    
    this.subscriptions.set(id, {
      id,
      channel,
      callback
    });

    return id;
  }

  // 구독 해제
  unsubscribe(subscriptionId: string) {
    this.subscriptions.delete(subscriptionId);
  }

  // 메시지 처리
  private handleMessage(message: RealtimeMessage) {
    for (const subscription of this.subscriptions.values()) {
      if (message.type === subscription.channel || message.type === 'broadcast') {
        try {
          subscription.callback(message);
        } catch (error) {
          console.error(`Error in SSE subscription callback for ${subscription.channel}:`, error);
        }
      }
    }
  }
}

// 실시간 데이터 관리자 (Singleton)
class RealtimeDataManager {
  private wsManager: WebSocketManager;
  private sseManager: SSEManager;

  constructor() {
    this.wsManager = new WebSocketManager();
    this.sseManager = new SSEManager();
  }

  // WebSocket 사용
  get ws() {
    return this.wsManager;
  }

  // SSE 사용
  get sse() {
    return this.sseManager;
  }

  // 정리
  cleanup() {
    this.wsManager.disconnect();
    this.sseManager.disconnectAll();
  }
}

// 전역 인스턴스
export const realtimeManager = new RealtimeDataManager();

// 실시간 데이터 훅을 위한 타입
export interface RealtimeHookOptions {
  channel: string;
  autoConnect?: boolean;
  reconnect?: boolean;
  useSSE?: boolean;
  sseEndpoint?: string;
}
