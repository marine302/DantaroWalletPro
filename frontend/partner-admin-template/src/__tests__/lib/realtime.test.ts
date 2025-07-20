/**
 * 실시간 데이터 처리 테스트
 */

import { WebSocketManager, SSEManager, realtimeManager } from '@/lib/realtime'

describe('WebSocketManager', () => {
  let wsManager: WebSocketManager
  let mockWebSocket: any

  beforeEach(() => {
    wsManager = new WebSocketManager('ws://test.com')
    
    mockWebSocket = {
      readyState: WebSocket.CONNECTING,
      send: jest.fn(),
      close: jest.fn(),
      onopen: null,
      onmessage: null,
      onclose: null,
      onerror: null
    }

    // Mock WebSocket constructor
    global.WebSocket = jest.fn().mockImplementation(() => mockWebSocket)
  })

  afterEach(() => {
    jest.resetAllMocks()
  })

  describe('Connection Management', () => {
    it('connects successfully', async () => {
      const connectPromise = wsManager.connect()
      
      // Simulate successful connection
      mockWebSocket.readyState = WebSocket.OPEN
      if (mockWebSocket.onopen) mockWebSocket.onopen()

      await expect(connectPromise).resolves.toBeUndefined()
    })

    it('handles connection errors', async () => {
      const connectPromise = wsManager.connect()
      
      // Simulate connection error
      const error = new Error('Connection failed')
      if (mockWebSocket.onerror) mockWebSocket.onerror(error)

      await expect(connectPromise).rejects.toThrow('Connection failed')
    })

    it('disconnects properly', () => {
      wsManager['ws'] = mockWebSocket
      wsManager.disconnect()

      expect(mockWebSocket.close).toHaveBeenCalled()
    })
  })

  describe('Message Handling', () => {
    beforeEach(async () => {
      const connectPromise = wsManager.connect()
      mockWebSocket.readyState = WebSocket.OPEN
      if (mockWebSocket.onopen) mockWebSocket.onopen()
      await connectPromise
    })

    it('sends messages correctly', () => {
      const message = { type: 'test', data: 'hello' }
      wsManager.send(message)

      expect(mockWebSocket.send).toHaveBeenCalledWith(JSON.stringify(message))
    })

    it('handles incoming messages', () => {
      const callback = jest.fn()
      const subscriptionId = wsManager.subscribe('test-channel', callback)

      const message = {
        type: 'test-channel',
        payload: { data: 'test' },
        timestamp: new Date().toISOString()
      }

      // Simulate incoming message
      if (mockWebSocket.onmessage) {
        mockWebSocket.onmessage({
          data: JSON.stringify(message)
        })
      }

      expect(callback).toHaveBeenCalledWith(message)
    })

    it('handles subscription and unsubscription', () => {
      const callback = jest.fn()
      const subscriptionId = wsManager.subscribe('test-channel', callback)

      expect(subscriptionId).toBeDefined()
      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({ type: 'subscribe', channel: 'test-channel' })
      )

      wsManager.unsubscribe(subscriptionId)
      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({ type: 'unsubscribe', channel: 'test-channel' })
      )
    })
  })

  describe('Connection State', () => {
    it('reports connection state correctly', () => {
      wsManager['ws'] = mockWebSocket
      
      mockWebSocket.readyState = WebSocket.OPEN
      expect(wsManager.isConnected).toBe(true)
      
      mockWebSocket.readyState = WebSocket.CLOSED
      expect(wsManager.isConnected).toBe(false)
    })
  })
})

describe('SSEManager', () => {
  let sseManager: SSEManager
  let mockEventSource: any

  beforeEach(() => {
    sseManager = new SSEManager()
    
    mockEventSource = {
      close: jest.fn(),
      onopen: null,
      onmessage: null,
      onerror: null
    }

    // Mock EventSource constructor
    global.EventSource = jest.fn().mockImplementation(() => mockEventSource)
  })

  afterEach(() => {
    jest.resetAllMocks()
  })

  describe('Connection Management', () => {
    it('connects successfully', async () => {
      const connectPromise = sseManager.connect('/events', ['channel1'])
      
      // Simulate successful connection
      if (mockEventSource.onopen) mockEventSource.onopen()

      const connectionId = await connectPromise
      expect(connectionId).toBeDefined()
      expect(connectionId).toMatch(/^sse_/)
    })

    it('handles connection errors', async () => {
      const connectPromise = sseManager.connect('/events')
      
      // Simulate connection error
      const error = new Error('SSE connection failed')
      if (mockEventSource.onerror) mockEventSource.onerror(error)

      await expect(connectPromise).rejects.toThrow('SSE connection failed')
    })

    it('disconnects specific connection', () => {
      sseManager['eventSources'].set('test-id', mockEventSource)
      sseManager.disconnect('test-id')

      expect(mockEventSource.close).toHaveBeenCalled()
    })

    it('disconnects all connections', () => {
      sseManager['eventSources'].set('test-id-1', mockEventSource)
      sseManager['eventSources'].set('test-id-2', { close: jest.fn() })
      
      sseManager.disconnectAll()

      expect(mockEventSource.close).toHaveBeenCalled()
      expect(sseManager['eventSources'].size).toBe(0)
    })
  })

  describe('Message Handling', () => {
    it('handles incoming messages', () => {
      const callback = jest.fn()
      sseManager.subscribe('test-channel', callback)

      const message = {
        type: 'test-channel',
        payload: { data: 'test' },
        timestamp: new Date().toISOString()
      }

      // Simulate incoming message
      if (mockEventSource.onmessage) {
        mockEventSource.onmessage({
          data: JSON.stringify(message)
        })
      }

      expect(callback).toHaveBeenCalledWith(message)
    })

    it('manages subscriptions correctly', () => {
      const callback = jest.fn()
      const subscriptionId = sseManager.subscribe('test-channel', callback)

      expect(subscriptionId).toBeDefined()
      expect(sseManager['subscriptions'].has(subscriptionId)).toBe(true)

      sseManager.unsubscribe(subscriptionId)
      expect(sseManager['subscriptions'].has(subscriptionId)).toBe(false)
    })
  })
})

describe('Realtime Manager', () => {
  it('provides WebSocket and SSE managers', () => {
    expect(realtimeManager.ws).toBeInstanceOf(WebSocketManager)
    expect(realtimeManager.sse).toBeInstanceOf(SSEManager)
  })

  it('cleans up connections properly', () => {
    const wsSpy = jest.spyOn(realtimeManager.ws, 'disconnect')
    const sseSpy = jest.spyOn(realtimeManager.sse, 'disconnectAll')

    realtimeManager.cleanup()

    expect(wsSpy).toHaveBeenCalled()
    expect(sseSpy).toHaveBeenCalled()
  })
})
