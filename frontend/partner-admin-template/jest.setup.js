import '@testing-library/jest-dom'

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
global.localStorage = localStorageMock

// Mock fetch
global.fetch = jest.fn()

// Mock WebSocket
global.WebSocket = class WebSocket {
  constructor(url) {
    this.url = url
    this.readyState = WebSocket.CONNECTING
    setTimeout(() => {
      this.readyState = WebSocket.OPEN
      if (this.onopen) this.onopen()
    }, 0)
  }
  
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3
  
  send = jest.fn()
  close = jest.fn()
  onopen = null
  onmessage = null
  onclose = null
  onerror = null
}

// Mock EventSource
global.EventSource = class EventSource {
  constructor(url) {
    this.url = url
    this.readyState = EventSource.CONNECTING
    setTimeout(() => {
      this.readyState = EventSource.OPEN
      if (this.onopen) this.onopen()
    }, 0)
  }
  
  static CONNECTING = 0
  static OPEN = 1
  static CLOSED = 2
  
  close = jest.fn()
  onopen = null
  onmessage = null
  onerror = null
}
