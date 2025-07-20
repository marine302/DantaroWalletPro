// Notification priority levels (enum for runtime values)
export enum NotificationPriority {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low'
}

// Notification channels (enum for runtime values)
export enum NotificationChannel {
  SYSTEM = 'system',
  SECURITY = 'security',
  TRADING = 'trading',
  PARTNER = 'partner',
  COMPLIANCE = 'compliance'
}

// Notification types
export type NotificationType = 'info' | 'warning' | 'error' | 'success';

// Action interface for notification buttons
export interface NotificationAction {
  label: string;
  action: () => void;
}

// Main notification interface
export interface Notification {
  id: string;
  title: string;
  message: string;
  priority: NotificationPriority;
  channel: NotificationChannel;
  type: NotificationType;
  timestamp: Date;
  read: boolean;
  actions?: NotificationAction[];
}

// Notification settings interface
export interface NotificationSettings {
  enabled: boolean;
  soundEnabled: boolean;
  pushEnabled: boolean;
  emailEnabled: boolean;
  priorities: Record<NotificationPriority, boolean>;
  channels: Record<NotificationChannel, boolean>;
  maxActiveNotifications: number;
  autoMarkAsRead: boolean;
  historyRetentionDays: number;
}

// Filter interface for notification queries
export interface NotificationFilter {
  priorities: NotificationPriority[];
  channels: NotificationChannel[];
  dateRange: { start: Date; end: Date } | null;
  readStatus: 'all' | 'read' | 'unread';
  searchQuery: string;
}

// Statistics interface
export interface NotificationStats {
  total: number;
  unread: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  byChannel: Record<NotificationChannel, number>;
}

// Sound configuration
export interface NotificationSoundConfig {
  enabled: boolean;
  volume: number;
  sounds: Record<NotificationPriority, string>;
}

// Type guards for runtime type checking
export function isNotificationPriority(value: string): value is NotificationPriority {
  return Object.values(NotificationPriority).includes(value as NotificationPriority);
}

export function isNotificationChannel(value: string): value is NotificationChannel {
  return Object.values(NotificationChannel).includes(value as NotificationChannel);
}

export function isNotificationType(value: string): value is NotificationType {
  return ['info', 'warning', 'error', 'success'].includes(value);
}
