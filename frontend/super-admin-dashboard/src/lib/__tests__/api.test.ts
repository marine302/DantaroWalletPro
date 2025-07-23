import { apiClient } from '../api';
import { mockApiResponse, mockApiError } from '@/test-utils/test-utils';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('API Client', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    // Clear localStorage
    localStorage.clear();
  });

  describe('getDashboardStats', () => {
    it('returns dashboard stats from backend API when available', async () => {
      const mockStats = {
        total_users: 1500,
        active_partners: 25,
        total_revenue: 1250000,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockApiResponse(mockStats),
      });

      const result = await apiClient.getDashboardStats();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/admin/dashboard/overview',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );

      expect(result).toEqual(mockStats);
    });

    it('falls back to mock API when backend fails', async () => {
      // First call to backend fails
      mockFetch.mockRejectedValueOnce(new Error('Backend unavailable'));

      // Second call to mock API succeeds
      const mockStats = { total_users: 100, active_partners: 5 };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats,
      });

      const result = await apiClient.getDashboardStats();

      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(mockFetch).toHaveBeenNthCalledWith(2,
        'http://localhost:3001/api/dashboard/stats',
        expect.any(Object)
      );

      expect(result).toEqual(mockStats);
    });

    it('returns default data when all APIs fail', async () => {
      mockFetch.mockRejectedValue(new Error('All APIs failed'));

      const result = await apiClient.getDashboardStats();

      expect(result).toEqual({
        total_users: 0,
        active_partners: 0,
        total_revenue: 0,
        available_energy: 0,
        daily_volume: 0,
        total_transactions_today: 0,
        active_wallets: 0,
      });
    });
  });

  describe('login', () => {
    it('successfully authenticates with valid credentials', async () => {
      const mockResponse = {
        token: 'mock-jwt-token',
        user: { id: '1', email: 'admin@test.com', role: 'super_admin' },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockApiResponse(mockResponse),
      });

      const result = await apiClient.login('admin@test.com', 'password');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/auth/super-admin/login',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            email: 'admin@test.com',
            password: 'password',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    it('throws error for invalid credentials', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => mockApiError('Invalid credentials'),
      });

      await expect(
        apiClient.login('invalid@test.com', 'wrongpassword')
      ).rejects.toThrow('Invalid credentials');
    });
  });

  describe('getPartners', () => {
    it('fetches partners with pagination', async () => {
      const mockPartners = {
        partners: [
          { id: '1', name: 'Partner 1', status: 'active' },
          { id: '2', name: 'Partner 2', status: 'pending' },
        ],
        total: 2,
        page: 1,
        limit: 10,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockApiResponse(mockPartners),
      });

      const result = await apiClient.getPartners(1, 10);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/partners/?page=1&limit=10',
        expect.any(Object)
      );

      expect(result).toEqual(mockPartners);
    });

    it('handles search parameters correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockApiResponse({ partners: [], total: 0 }),
      });

      await apiClient.getPartners(1, 10, 'search term');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/partners/?page=1&limit=10&search=search%20term',
        expect.any(Object)
      );
    });
  });

  describe('authentication headers', () => {
    it('includes authorization header when token is available', async () => {
      localStorage.setItem('authToken', 'test-token');

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockApiResponse({}),
      });

      await apiClient.getDashboardStats();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
          }),
        })
      );
    });

    it('does not include authorization header when no token', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockApiResponse({}),
      });

      await apiClient.getDashboardStats();

      const headers = mockFetch.mock.calls[0][1].headers;
      expect(headers).not.toHaveProperty('Authorization');
    });
  });

  describe('error handling', () => {
    it('handles network errors gracefully', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      const result = await apiClient.getDashboardStats();

      // Should return default data instead of throwing
      expect(result).toBeDefined();
      expect(typeof result).toBe('object');
    });

    it('handles HTTP error responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => mockApiError('Internal server error'),
      });

      // Should fallback to mock API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ total_users: 100 }),
      });

      const result = await apiClient.getDashboardStats();

      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(result).toBeDefined();
    });
  });
});
