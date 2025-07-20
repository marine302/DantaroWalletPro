/**
 * 사용자 관리 서비스 - 실제 API 연동 및 로컬 상태 관리
 */

import type { User, UserStats } from '../../types';

export interface UserFilters {
  search?: string;
  status?: 'active' | 'inactive' | 'suspended' | 'pending';
  kycStatus?: 'none' | 'pending' | 'approved' | 'rejected';
  tier?: 'basic' | 'premium' | 'vip';
  dateFrom?: string;
  dateTo?: string;
}

export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  phone?: string;
  wallet_address?: string;
  tier?: 'basic' | 'premium' | 'vip';
  send_welcome_email?: boolean;
}

export interface UpdateUserRequest {
  username?: string;
  email?: string;
  phone?: string;
  status?: 'active' | 'inactive' | 'suspended';
  tier?: 'basic' | 'premium' | 'vip';
  kyc_status?: 'none' | 'pending' | 'approved' | 'rejected';
}

// Mock 데이터 생성 함수
const generateMockUsers = (count: number = 50): User[] => {
  const users: User[] = [];
  const statuses: ('active' | 'inactive' | 'suspended' | 'pending')[] = ['active', 'inactive', 'suspended', 'pending'];
  const kycStatuses: ('pending' | 'approved' | 'rejected' | 'not_started')[] = ['not_started', 'pending', 'approved', 'rejected'];
  const tiers: ('basic' | 'premium' | 'vip')[] = ['basic', 'premium', 'vip'];

  for (let i = 1; i <= count; i++) {
    const createdDate = new Date(2024, Math.floor(Math.random() * 7), Math.floor(Math.random() * 28) + 1);
    const lastLoginDate = new Date(createdDate.getTime() + Math.random() * (Date.now() - createdDate.getTime()));
    
    users.push({
      id: i.toString(),
      username: `user_${i.toString().padStart(3, '0')}`,
      email: `user${i}@example.com`,
      walletAddress: `TR${Math.random().toString(36).substring(2, 32).toUpperCase()}`,
      balance: Math.floor(Math.random() * 100000 * 100) / 100,
      status: statuses[Math.floor(Math.random() * statuses.length)] as 'active' | 'inactive' | 'suspended',
      kycStatus: kycStatuses[Math.floor(Math.random() * kycStatuses.length)] as 'pending' | 'approved' | 'rejected' | 'not_started',
      createdAt: createdDate.toISOString(),
      lastLogin: Math.random() > 0.2 ? lastLoginDate.toISOString() : new Date().toISOString(),
      totalTransactions: Math.floor(Math.random() * 200),
      totalVolume: Math.floor(Math.random() * 500000 * 100) / 100
    });
  }

  return users;
};

// 로컬 스토리지 기반 사용자 데이터 관리
class UserDataManager {
  private static readonly STORAGE_KEY = 'user_management_data';
  private static readonly STATS_STORAGE_KEY = 'user_stats_data';

  static initializeData(): void {
    if (typeof window === 'undefined') return;
    
    const existing = localStorage.getItem(this.STORAGE_KEY);
    if (!existing) {
      const mockUsers = generateMockUsers(50);
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(mockUsers));
      this.updateStats();
    }
  }

  static getAllUsers(): User[] {
    if (typeof window === 'undefined') return [];
    
    const data = localStorage.getItem(this.STORAGE_KEY);
    return data ? JSON.parse(data) : [];
  }

  static saveUsers(users: User[]): void {
    if (typeof window === 'undefined') return;
    
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(users));
    this.updateStats();
  }

  static getUserById(id: string): User | null {
    const users = this.getAllUsers();
    return users.find(user => user.id === id) || null;
  }

  static updateStats(): void {
    if (typeof window === 'undefined') return;
    
    const users = this.getAllUsers();
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    
    const stats: UserStats = {
      totalUsers: users.length,
      activeUsers: users.filter(u => u.status === 'active').length,
      newUsersToday: users.filter(u => new Date(u.createdAt) >= today).length,
      totalBalance: users.reduce((sum, u) => sum + u.balance, 0),
      averageBalance: users.length > 0 ? users.reduce((sum, u) => sum + u.balance, 0) / users.length : 0,
      kycApproved: users.filter(u => u.kycStatus === 'approved').length,
      kycPending: users.filter(u => u.kycStatus === 'pending').length,
      dailyGrowth: Math.random() * 10 - 5, // Mock
      weeklyGrowth: Math.random() * 30 - 15, // Mock
      monthlyGrowth: Math.random() * 50 - 25 // Mock
    };

    localStorage.setItem(this.STATS_STORAGE_KEY, JSON.stringify(stats));
  }

  static getStats(): UserStats {
    if (typeof window === 'undefined') {
      return {
        totalUsers: 0,
        activeUsers: 0,
        newUsersToday: 0,
        totalBalance: 0,
        averageBalance: 0,
        kycApproved: 0,
        kycPending: 0,
        dailyGrowth: 0,
        weeklyGrowth: 0,
        monthlyGrowth: 0
      };
    }

    const data = localStorage.getItem(this.STATS_STORAGE_KEY);
    if (data) {
      return JSON.parse(data);
    }

    // 통계 데이터가 없으면 생성
    this.updateStats();
    const newData = localStorage.getItem(this.STATS_STORAGE_KEY);
    return newData ? JSON.parse(newData) : {};
  }
}

// UserService 클래스 정의
class UserService {
  /**
   * 사용자 목록 조회 (필터링, 페이지네이션 지원)
   */
  async getUsers(
    page: number = 1,
    limit: number = 20,
    filters: UserFilters = {}
  ): Promise<UserListResponse> {
    try {
      // 개발 환경에서는 로컬 데이터 사용
      const allUsers = UserDataManager.getAllUsers();
      let filteredUsers = [...allUsers];

      // 검색 필터 적용
      if (filters.search) {
        const searchTerm = filters.search.toLowerCase();
        filteredUsers = filteredUsers.filter(user =>
          user.username.toLowerCase().includes(searchTerm) ||
          user.email.toLowerCase().includes(searchTerm) ||
          user.walletAddress.toLowerCase().includes(searchTerm) ||
          (user.phone && user.phone.includes(searchTerm))
        );
      }

      // 상태 필터 적용
      if (filters.status) {
        filteredUsers = filteredUsers.filter(user => user.status === filters.status);
      }

      // KYC 상태 필터 적용
      if (filters.kycStatus) {
        filteredUsers = filteredUsers.filter(user => user.kycStatus === filters.kycStatus);
      }

      // 티어 필터 적용
      if (filters.tier) {
        filteredUsers = filteredUsers.filter(user => user.tier === filters.tier);
      }

      // 날짜 필터 적용
      if (filters.dateFrom) {
        const fromDate = new Date(filters.dateFrom);
        filteredUsers = filteredUsers.filter(user => new Date(user.createdAt) >= fromDate);
      }

      if (filters.dateTo) {
        const toDate = new Date(filters.dateTo);
        filteredUsers = filteredUsers.filter(user => new Date(user.createdAt) <= toDate);
      }

      // 페이지네이션 적용
      const total = filteredUsers.length;
      const totalPages = Math.ceil(total / limit);
      const startIndex = (page - 1) * limit;
      const endIndex = startIndex + limit;
      const paginatedUsers = filteredUsers.slice(startIndex, endIndex);

      // 실제 API 호출 시뮬레이션을 위한 딜레이
      await new Promise(resolve => setTimeout(resolve, 300));

      return {
        users: paginatedUsers,
        total,
        page,
        limit,
        totalPages
      };
    } catch (error) {
      console.error('Failed to fetch users:', error);
      throw error;
    }
  }

  /**
   * 사용자 통계 조회
   */
  async getUserStats(): Promise<UserStats> {
    try {
      // 개발 환경에서는 로컬 데이터 사용
      const stats = UserDataManager.getStats();
      
      // 실제 API 호출 시뮬레이션을 위한 딜레이
      await new Promise(resolve => setTimeout(resolve, 200));

      return stats;
    } catch (error) {
      console.error('Failed to fetch user stats:', error);
      throw error;
    }
  }

  /**
   * 사용자 생성
   */
  async createUser(userData: CreateUserRequest): Promise<User> {
    try {
      const users = UserDataManager.getAllUsers();
      const newId = (Math.max(...users.map(u => parseInt(u.id))) + 1).toString();

      const newUser: User = {
        id: newId,
        username: userData.username,
        email: userData.email,
        phone: userData.phone,
        walletAddress: userData.wallet_address || `TR${Math.random().toString(36).substring(2, 32).toUpperCase()}`,
        balance: 0,
        status: 'active',
        kycStatus: 'none',
        tier: userData.tier || 'basic',
        createdAt: new Date().toISOString(),
        totalTransactions: 0,
        totalVolume: 0,
        referralCode: `REF${newId.padStart(4, '0')}`
      };

      users.push(newUser);
      UserDataManager.saveUsers(users);

      await new Promise(resolve => setTimeout(resolve, 500));

      return newUser;
    } catch (error) {
      console.error('Failed to create user:', error);
      throw error;
    }
  }

  /**
   * 사용자 정보 수정
   */
  async updateUser(userId: string, updates: UpdateUserRequest): Promise<User> {
    try {
      const users = UserDataManager.getAllUsers();
      const userIndex = users.findIndex(u => u.id === userId);

      if (userIndex === -1) {
        throw new Error('User not found');
      }

      users[userIndex] = { ...users[userIndex], ...updates };
      UserDataManager.saveUsers(users);

      await new Promise(resolve => setTimeout(resolve, 400));

      return users[userIndex];
    } catch (error) {
      console.error('Failed to update user:', error);
      throw error;
    }
  }

  /**
   * 사용자 삭제
   */
  async deleteUser(userId: string): Promise<void> {
    try {
      const users = UserDataManager.getAllUsers();
      const filteredUsers = users.filter(u => u.id !== userId);

      if (filteredUsers.length === users.length) {
        throw new Error('User not found');
      }

      UserDataManager.saveUsers(filteredUsers);

      await new Promise(resolve => setTimeout(resolve, 300));
    } catch (error) {
      console.error('Failed to delete user:', error);
      throw error;
    }
  }

  /**
   * 벌크 액션 실행
   */
  async bulkUpdateUsers(userIds: string[], updates: Partial<UpdateUserRequest>): Promise<User[]> {
    try {
      const users = UserDataManager.getAllUsers();
      const updatedUsers: User[] = [];

      users.forEach(user => {
        if (userIds.includes(user.id)) {
          Object.assign(user, updates);
          updatedUsers.push(user);
        }
      });

      UserDataManager.saveUsers(users);

      await new Promise(resolve => setTimeout(resolve, 600));

      return updatedUsers;
    } catch (error) {
      console.error('Failed to bulk update users:', error);
      throw error;
    }
  }

  /**
   * 사용자 데이터 내보내기
   */
  async exportUsers(filters: UserFilters = {}): Promise<string> {
    try {
      const response = await this.getUsers(1, 10000, filters); // 모든 데이터 가져오기
      const users = response.users;

      // CSV 형식으로 변환
      const headers = [
        'ID', 'Username', 'Email', 'Phone', 'Wallet Address', 'Balance',
        'Status', 'KYC Status', 'Tier', 'Created At', 'Last Login',
        'Total Transactions', 'Total Volume', 'Referral Code'
      ];

      const csvData = [
        headers.join(','),
        ...users.map(user => [
          user.id,
          user.username,
          user.email,
          user.phone || '',
          user.walletAddress,
          user.balance,
          user.status,
          user.kycStatus,
          user.tier,
          user.createdAt,
          user.lastLogin || '',
          user.totalTransactions,
          user.totalVolume,
          user.referralCode || ''
        ].join(','))
      ].join('\n');

      return csvData;
    } catch (error) {
      console.error('Failed to export users:', error);
      throw error;
    }
  }
};

// UserService 인스턴스 생성 및 export
export const userService = new UserService();

// 초기 데이터 설정
if (typeof window !== 'undefined') {
  UserDataManager.initializeData();
}
