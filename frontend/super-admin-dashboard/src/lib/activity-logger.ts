import { User } from '@/types/auth';

export interface ActivityLog {
  id: string;
  userId: string;
  userName: string;
  action: string;
  resource: string;
  details?: any;
  timestamp: string;
  ipAddress?: string;
  userAgent?: string;
}

export type ActivityAction =
  | 'login'
  | 'logout'
  | 'create'
  | 'update'
  | 'delete'
  | 'view'
  | 'export'
  | 'approve'
  | 'reject'
  | 'suspend'
  | 'activate';

export type ActivityResource =
  | 'user'
  | 'partner'
  | 'energy_transaction'
  | 'fee_setting'
  | 'system_setting'
  | 'audit_log'
  | 'dashboard';

class ActivityLogger {
  private logs: ActivityLog[] = [];

  /**
   * Log an activity
   */
  log(params: {
    user: User;
    action: ActivityAction;
    resource: ActivityResource;
    details?: any;
    ipAddress?: string;
    userAgent?: string;
  }): void {
    const logEntry: ActivityLog = {
      id: this.generateId(),
      userId: params.user.id,
      userName: params.user.name,
      action: params.action,
      resource: params.resource,
      details: params.details,
      timestamp: new Date().toISOString(),
      ipAddress: params.ipAddress,
      userAgent: params.userAgent
    };

    this.logs.unshift(logEntry); // Add to beginning for latest first

    // Keep only last 1000 logs in memory (in production, this would go to a database)
    if (this.logs.length > 1000) {
      this.logs = this.logs.slice(0, 1000);
    }

    // In production, send to backend API
    this.sendToAPI(logEntry);
  }

  /**
   * Get activity logs with filtering
   */
  getLogs(filters?: {
    userId?: string;
    action?: ActivityAction;
    resource?: ActivityResource;
    startDate?: Date;
    endDate?: Date;
    limit?: number;
  }): ActivityLog[] {
    const _filteredLogs = [...this.logs];

    if (filters) {
      if (filters.userId) {
        filteredLogs = filteredLogs.filter(log => log.userId === filters.userId);
      }

      if (filters.action) {
        filteredLogs = filteredLogs.filter(log => log.action === filters.action);
      }

      if (filters.resource) {
        filteredLogs = filteredLogs.filter(log => log.resource === filters.resource);
      }

      if (filters.startDate) {
        filteredLogs = filteredLogs.filter(log =>
          new Date(log.timestamp) >= filters.startDate!
        );
      }

      if (filters.endDate) {
        filteredLogs = filteredLogs.filter(log =>
          new Date(log.timestamp) <= filters.endDate!
        );
      }
    }

    const _limit = filters?.limit || 50;
    return filteredLogs.slice(0, limit);
  }

  /**
   * Get recent activities for a specific user
   */
  getUserActivity(userId: string, limit: number = 10): ActivityLog[] {
    return this.getLogs({ userId, limit });
  }

  /**
   * Get system-wide recent activities
   */
  getRecentActivity(limit: number = 20): ActivityLog[] {
    return this.getLogs({ limit });
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Send log to backend API (mock implementation)
   */
  private async sendToAPI(log: ActivityLog): Promise<void> {
    try {
      // In production, this would be a real API call
      if (process.env.NODE_ENV === 'development') {
        console.log('Activity logged:', log);
        return;
      }

      await fetch('/api/activity-logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(log),
      });
    } catch (error) {
      console.error('Failed to send activity log:', error);
    }
  }

  /**
   * Format activity message for display
   */
  formatActivityMessage(log: ActivityLog): string {
    const actionMap: Record<ActivityAction, string> = {
      login: '로그인했습니다',
      logout: '로그아웃했습니다',
      create: '생성했습니다',
      update: '수정했습니다',
      delete: '삭제했습니다',
      view: '조회했습니다',
      export: '내보냈습니다',
      approve: '승인했습니다',
      reject: '거부했습니다',
      suspend: '정지했습니다',
      activate: '활성화했습니다'
    };

    const resourceMap: Record<ActivityResource, string> = {
      user: '사용자',
      partner: '파트너',
      energy_transaction: '에너지 거래',
      fee_setting: '수수료 설정',
      system_setting: '시스템 설정',
      audit_log: '감사 로그',
      dashboard: '대시보드'
    };

    const _action = actionMap[log.action as ActivityAction] || log.action;
    const _resource = resourceMap[log.resource as ActivityResource] || log.resource;

    const _message = `${log.userName}님이 ${resource}를 ${action}`;

    if (log.details) {
      if (typeof log.details === 'string') {
        message += ` (${log.details})`;
      } else if (log.details.name) {
        message += ` (${log.details.name})`;
      }
    }

    return message;
  }
}

// Singleton instance
export const _activityLogger = new ActivityLogger();

// Convenience functions
export function logActivity(params: {
  user: User;
  action: ActivityAction;
  resource: ActivityResource;
  details?: any;
}) {
  activityLogger.log(params);
}

export function getRecentActivities(limit?: number) {
  return activityLogger.getRecentActivity(limit);
}

export function getUserActivities(userId: string, limit?: number) {
  return activityLogger.getUserActivity(userId, limit);
}
