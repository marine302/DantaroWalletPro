/**
 * API 클라이언트 테스트
 */

import { ApiClient, apiClient, handleApiError } from '@/lib/api-client'

// Mock fetch for testing
const mockFetch = jest.fn()
global.fetch = mockFetch

describe('ApiClient', () => {
  let client: ApiClient

  beforeEach(() => {
    client = new ApiClient('http://test-api.com', 5000)
    mockFetch.mockClear()
  })

  afterEach(() => {
    jest.resetAllMocks()
  })

  describe('Authentication', () => {
    it('sets auth token correctly', () => {
      const token = 'test-token-123'
      client.setAuthToken(token)
      
      // 토큰이 설정되었는지 내부적으로 확인
      expect(client['authToken']).toBe(token)
    })

    it('clears auth token correctly', () => {
      client.setAuthToken('test-token')
      client.clearAuthToken()
      
      expect(client['authToken']).toBeUndefined()
    })

    it('includes auth header when token is set', async () => {
      const token = 'test-token-123'
      client.setAuthToken(token)

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: {} })
      })

      await client.get('/test')

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': `Bearer ${token}`
          })
        })
      )
    })
  })

  describe('HTTP Methods', () => {
    beforeEach(() => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true, data: { id: 1 } })
      })
    })

    it('makes GET requests correctly', async () => {
      await client.get('/users')

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/users',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      )
    })

    it('makes POST requests correctly', async () => {
      const data = { name: 'Test User' }
      await client.post('/users', data)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/users',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify(data)
        })
      )
    })

    it('makes PUT requests correctly', async () => {
      const data = { name: 'Updated User' }
      await client.put('/users/1', data)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/users/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(data)
        })
      )
    })

    it('makes PATCH requests correctly', async () => {
      const data = { name: 'Patched User' }
      await client.patch('/users/1', data)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/users/1',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify(data)
        })
      )
    })

    it('makes DELETE requests correctly', async () => {
      await client.delete('/users/1')

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/users/1',
        expect.objectContaining({
          method: 'DELETE'
        })
      )
    })
  })

  describe('Error Handling', () => {
    it('handles HTTP errors correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: () => Promise.resolve({ message: 'User not found' })
      })

      const result = await client.get('/users/999')

      expect(result.success).toBe(false)
      expect(result.error).toBe('User not found')
    })

    it('handles network errors correctly', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const result = await client.get('/users')

      expect(result.success).toBe(false)
      expect(result.error).toBe('Network error')
    })

    it('handles timeout correctly', async () => {
      mockFetch.mockImplementationOnce(() => 
        new Promise(resolve => setTimeout(resolve, 10000))
      )

      const result = await client.get('/users')

      expect(result.success).toBe(false)
      expect(result.error).toContain('aborted')
    })
  })

  describe('Response Handling', () => {
    it('handles successful responses correctly', async () => {
      const mockData = { id: 1, name: 'Test User' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: mockData })
      })

      const result = await client.get('/users/1')

      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockData)
    })

    it('handles empty responses correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true })
      })

      const result = await client.get('/users')

      expect(result.success).toBe(true)
      expect(result.data).toBeUndefined()
    })
  })
})

describe('Error Handler Utility', () => {
  it('extracts error message correctly', () => {
    const apiResponse = {
      success: false,
      error: 'Test error message'
    }

    const errorMessage = handleApiError(apiResponse)
    expect(errorMessage).toBe('Test error message')
  })

  it('provides default error message when none exists', () => {
    const apiResponse = {
      success: false
    }

    const errorMessage = handleApiError(apiResponse)
    expect(errorMessage).toBe('Unknown error occurred')
  })
})

describe('Global API Client', () => {
  it('exports a configured instance', () => {
    expect(apiClient).toBeInstanceOf(ApiClient)
  })
})
