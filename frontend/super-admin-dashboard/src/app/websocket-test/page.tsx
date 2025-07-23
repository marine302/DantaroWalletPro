'use client';

import { useEffect, useState } from 'react';
import { Button, Section } from '@/components/ui/DarkThemeComponents';
import BasePage from '@/components/ui/BasePage';

export default function WebSocketTestPage() {
  const [connectionStatus, setConnectionStatus] = useState('Not connected');
  const [messages, setMessages] = useState<string[]>([]);
  const [wsInstance, setWsInstance] = useState<WebSocket | null>(null);

  useEffect(() => {
    const _wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3002';
    console.log('🔌 Attempting to connect to WebSocket:', wsUrl);

    const _ws = new WebSocket(wsUrl);
    setWsInstance(ws);

    ws.onopen = () => {
      console.log('✅ WebSocket connected');
      setConnectionStatus('Connected');
      setMessages(prev => [...prev, `✅ Connected to ${wsUrl} at ${new Date().toLocaleTimeString()}`]);
    };

    ws.onmessage = (event) => {
      try {
        const _data = JSON.parse(event.data);
        console.log('📨 Received data:', data);
        setMessages(prev => [...prev, `📨 ${data.type}: ${JSON.stringify(data, null, 2)}`]);
      } catch (error) {
        console.log('📨 Received text:', event.data);
        setMessages(prev => [...prev, `📨 Raw: ${event.data}`]);
      }
    };

    ws.onclose = (event) => {
      console.log('❌ WebSocket closed:', event.code, event.reason);
      setConnectionStatus('Disconnected');
      setMessages(prev => [...prev, `❌ Disconnected: ${event.code} ${event.reason || ''} at ${new Date().toLocaleTimeString()}`]);
    };

    ws.onerror = (error) => {
      console.error('🚨 WebSocket error:', error);
      setConnectionStatus('Error');
      setMessages(prev => [...prev, `🚨 Error occurred at ${new Date().toLocaleTimeString()}`]);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  const _sendTestMessage = () => {
    if (wsInstance && wsInstance.readyState === WebSocket.OPEN) {
      wsInstance.send(JSON.stringify({ type: 'ping', timestamp: new Date().toISOString() }));
      setMessages(prev => [...prev, `📤 Sent ping at ${new Date().toLocaleTimeString()}`]);
    }
  };

  const _clearMessages = () => {
    setMessages([]);
  };

  const _reconnect = () => {
    if (wsInstance) {
      wsInstance.close();
    }
    // useEffect will handle reconnection
    window.location.reload();
  };

  return (
    <BasePage
      title="🔗 WebSocket 연결 테스트"
      description="실시간 WebSocket 연결을 테스트하고 모니터링합니다"
    >
      {/* 연결 상태 */}
      <Section title="연결 상태">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              connectionStatus === 'Connected'
                ? 'bg-green-900/30 text-green-300'
                : connectionStatus === 'Error'
                ? 'bg-red-900/30 text-red-300'
                : 'bg-yellow-900/30 text-yellow-300'
            }`}>
              {connectionStatus}
            </span>
            <span className="text-gray-300">
              {process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3002'}
            </span>
          </div>
          <div className="space-x-2">
            <Button onClick={sendTestMessage} disabled={connectionStatus !== 'Connected'}>
              📤 Test Ping
            </Button>
            <Button onClick={reconnect} variant="secondary">
              🔄 Reconnect
            </Button>
          </div>
        </div>
      </Section>

      {/* 제어 패널 */}
      <Section title="제어 패널">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Button
            onClick={sendTestMessage}
            disabled={connectionStatus !== 'Connected'}
            className="w-full"
          >
            📡 Ping 전송
          </Button>
          <Button
            onClick={() => {
              if (wsInstance && wsInstance.readyState === WebSocket.OPEN) {
                wsInstance.send(JSON.stringify({ type: 'subscribe', channel: 'dashboardStats' }));
                setMessages(prev => [...prev, `📤 Subscribed to dashboardStats`]);
              }
            }}
            disabled={connectionStatus !== 'Connected'}
            className="w-full"
          >
            📊 대시보드 구독
          </Button>
          <Button
            onClick={() => {
              if (wsInstance && wsInstance.readyState === WebSocket.OPEN) {
                wsInstance.send(JSON.stringify({ type: 'subscribe', channel: 'energyMarket' }));
                setMessages(prev => [...prev, `📤 Subscribed to energyMarket`]);
              }
            }}
            disabled={connectionStatus !== 'Connected'}
            className="w-full"
          >
            ⚡ 에너지 구독
          </Button>
          <Button
            onClick={clearMessages}
            variant="danger"
            className="w-full"
          >
            🗑️ 로그 삭제
          </Button>
        </div>
      </Section>

      {/* 메시지 로그 */}
      <Section title="실시간 메시지 로그">
        <div className="bg-gray-800 rounded-lg p-4 h-96 overflow-y-auto">
          {messages.length === 0 ? (
            <p className="text-gray-400 text-center">메시지가 없습니다. 연결을 기다리거나 테스트 메시지를 전송해보세요.</p>
          ) : (
            <div className="space-y-2">
              {messages.map((message, index) => (
                <div key={index} className="text-sm">
                  <span className="text-gray-400">[{index + 1}]</span>{' '}
                  <span className="text-gray-100 font-mono">{message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </Section>

      {/* 환경 정보 */}
      <Section title="환경 설정">
        <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-4">
          <h4 className="text-blue-300 font-medium mb-2">🔧 현재 설정</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-400">WebSocket URL:</span>
              <span className="text-gray-100 ml-2 font-mono">
                {process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3002'}
              </span>
            </div>
            <div>
              <span className="text-gray-400">Mock Data:</span>
              <span className="text-gray-100 ml-2">
                {process.env.NEXT_PUBLIC_USE_MOCK_DATA || 'true'}
              </span>
            </div>
            <div>
              <span className="text-gray-400">Connection Status:</span>
              <span className="text-gray-100 ml-2">{connectionStatus}</span>
            </div>
            <div>
              <span className="text-gray-400">Messages Count:</span>
              <span className="text-gray-100 ml-2">{messages.length}</span>
            </div>
          </div>
        </div>
      </Section>
    </BasePage>
  );
}
