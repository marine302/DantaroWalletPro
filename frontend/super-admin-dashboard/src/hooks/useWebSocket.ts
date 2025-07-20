import { useCallback, useEffect, useRef, useState } from 'react';

interface WebSocketMessage {
  type: string;
  data: unknown;
  timestamp: string;
}

interface UseWebSocketOptions {
  reconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
}

interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  lastMessage: WebSocketMessage | null;
  error: string | null;
  reconnectCount: number;
}

export function useWebSocket(
  url: string,
  options: UseWebSocketOptions = {}
) {
  const {
    reconnectAttempts = 5,
    reconnectInterval = 3000,
    heartbeatInterval = 30000
  } = options;

  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const messageListeners = useRef<Map<string, Set<(data: unknown) => void>>>(new Map());

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    lastMessage: null,
    error: null,
    reconnectCount: 0
  });

  const connect = useCallback(() => {
    if (state.isConnecting || state.isConnected) return;

    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          reconnectCount: 0,
          error: null
        }));

        // Start heartbeat
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'ping' }));
          }
        }, heartbeatInterval);
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setState(prev => ({ ...prev, lastMessage: message }));

          // Notify specific listeners
          const listeners = messageListeners.current.get(message.type);
          if (listeners) {
            listeners.forEach(callback => callback(message.data));
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false
        }));

        // Clear heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
        }

        // Auto-reconnect if not manually closed
        if (event.code !== 1000 && state.reconnectCount < reconnectAttempts) {
          setState(prev => ({ ...prev, reconnectCount: prev.reconnectCount + 1 }));
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setState(prev => ({
          ...prev,
          error: 'Connection failed',
          isConnecting: false
        }));
      };

    } catch (error) {
      console.error('WebSocket connection error:', error);
      setState(prev => ({
        ...prev,
        error: 'Failed to create WebSocket connection',
        isConnecting: false
      }));
    }
  }, [url, reconnectAttempts, reconnectInterval, heartbeatInterval, state.isConnecting, state.isConnected, state.reconnectCount]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }
    if (ws.current) {
      ws.current.close(1000, 'Manual disconnect');
    }
    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
      reconnectCount: 0
    }));
  }, []);

  const sendMessage = useCallback((message: unknown) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  const subscribe = useCallback((messageType: string, callback: (data: unknown) => void) => {
    if (!messageListeners.current.has(messageType)) {
      messageListeners.current.set(messageType, new Set());
    }
    messageListeners.current.get(messageType)!.add(callback);

    // Return unsubscribe function
    return () => {
      const listeners = messageListeners.current.get(messageType);
      if (listeners) {
        listeners.delete(callback);
        if (listeners.size === 0) {
          messageListeners.current.delete(messageType);
        }
      }
    };
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    ...state,
    connect,
    disconnect,
    sendMessage,
    subscribe
  };
}
