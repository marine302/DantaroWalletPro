export type NotificationPriority = 'low' | 'medium' | 'high' | 'critical';

export type NotificationType = 
  | 'system'
  | 'security'
  | 'transaction'
  | 'partner'
  | 'user'
  | 'energy'
  | 'audit'
  | 'maintenance';

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: NotificationType;
  priority: NotificationPriority;
  timestamp: string;
  isRead: boolean;
  userId?: string;
  metadata?: any;
  actions?: NotificationAction[];
  expiresAt?: string;
}

export interface NotificationAction {
  id: string;
  label: string;
  action: 'approve' | 'reject' | 'view' | 'dismiss' | 'redirect';
  url?: string;
  variant?: 'primary' | 'secondary' | 'danger';
}

export interface NotificationSettings {
  userId: string;
  emailNotifications: boolean;
  pushNotifications: boolean;
  soundEnabled: boolean;
  priorities: {
    low: boolean;
    medium: boolean;
    high: boolean;
    critical: boolean;
  };
  types: {
    system: boolean;
    security: boolean;
    transaction: boolean;
    partner: boolean;
    user: boolean;
    energy: boolean;
    audit: boolean;
    maintenance: boolean;
  };
}

export interface NotificationStats {
  total: number;
  unread: number;
  byPriority: Record<NotificationPriority, number>;
  byType: Record<NotificationType, number>;
  recentCount: number;
}
