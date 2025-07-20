'use client';

import { useState, useEffect, useCallback } from 'react';
import { 
  notificationManager, 
  addNotification as addNotificationToManager,
  markAsRead as markNotificationAsRead,
  getNotifications as getNotificationsFromManager
} from '@/lib/notification-manager';
import { 
  Notification, 
  NotificationPriority, 
  NotificationType, 
  NotificationSettings,
  NotificationStats 
} from '@/types/notification';

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [stats, setStats] = useState<NotificationStats | null>(null);

  // Update state when notifications change
  useEffect(() => {
    const unsubscribe = notificationManager.subscribe((updatedNotifications) => {
      setNotifications(updatedNotifications);
      setStats(notificationManager.getStats());
    });

    // Initial load
    setNotifications(notificationManager.getNotifications());
    setSettings(notificationManager.getSettings());
    setStats(notificationManager.getStats());

    return unsubscribe;
  }, []);

  // Add notification
  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp' | 'isRead'>) => {
    return addNotificationToManager(notification);
  }, []);

  // Mark as read
  const markAsRead = useCallback((notificationId: string) => {
    markNotificationAsRead(notificationId);
  }, []);

  // Mark all as read
  const markAllAsRead = useCallback(() => {
    notificationManager.markAllAsRead();
  }, []);

  // Delete notification
  const deleteNotification = useCallback((notificationId: string) => {
    notificationManager.deleteNotification(notificationId);
  }, []);

  // Clear all notifications
  const clearAll = useCallback(() => {
    notificationManager.clearAll();
  }, []);

  // Get filtered notifications
  const getNotifications = useCallback((filters?: {
    type?: NotificationType;
    priority?: NotificationPriority;
    unreadOnly?: boolean;
    limit?: number;
  }) => {
    return getNotificationsFromManager(filters);
  }, []);

  // Update settings
  const updateSettings = useCallback((newSettings: Partial<NotificationSettings>) => {
    notificationManager.updateSettings(newSettings);
    setSettings(notificationManager.getSettings());
  }, []);

  // Request browser notification permission
  const requestPermission = useCallback(async () => {
    return await notificationManager.requestPermission();
  }, []);

  // Convenience getters
  const unreadCount = stats?.unread || 0;
  const recentCount = stats?.recentCount || 0;
  const unreadNotifications = notifications.filter(n => !n.isRead);
  const criticalNotifications = notifications.filter(n => n.priority === 'critical' && !n.isRead);

  return {
    // Data
    notifications,
    unreadNotifications,
    criticalNotifications,
    settings,
    stats,
    
    // Counts
    unreadCount,
    recentCount,
    
    // Actions
    addNotification,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    clearAll,
    getNotifications,
    updateSettings,
    requestPermission
  };
}

// Hook for creating system notifications
export function useSystemNotifications() {
  const { addNotification } = useNotifications();

  const notifySuccess = useCallback((title: string, message: string) => {
    addNotification({
      title,
      message,
      type: 'system',
      priority: 'low'
    });
  }, [addNotification]);

  const notifyWarning = useCallback((title: string, message: string) => {
    addNotification({
      title,
      message,
      type: 'system',
      priority: 'medium'
    });
  }, [addNotification]);

  const notifyError = useCallback((title: string, message: string) => {
    addNotification({
      title,
      message,
      type: 'system',
      priority: 'high'
    });
  }, [addNotification]);

  const notifyCritical = useCallback((title: string, message: string) => {
    addNotification({
      title,
      message,
      type: 'security',
      priority: 'critical'
    });
  }, [addNotification]);

  const notifyUserAction = useCallback((action: string, userName: string) => {
    addNotification({
      title: '사용자 활동',
      message: `${userName}님이 ${action}을(를) 수행했습니다.`,
      type: 'user',
      priority: 'low'
    });
  }, [addNotification]);

  const notifyPartnerUpdate = useCallback((partnerName: string, action: string) => {
    addNotification({
      title: '파트너 업데이트',
      message: `${partnerName} 파트너가 ${action}되었습니다.`,
      type: 'partner',
      priority: 'medium'
    });
  }, [addNotification]);

  const notifyEnergyTransaction = useCallback((amount: number, type: 'buy' | 'sell') => {
    addNotification({
      title: '에너지 거래',
      message: `${amount}kWh 에너지가 ${type === 'buy' ? '구매' : '판매'}되었습니다.`,
      type: 'energy',
      priority: 'medium'
    });
  }, [addNotification]);

  const notifySecurityAlert = useCallback((message: string) => {
    addNotification({
      title: '보안 경고',
      message,
      type: 'security',
      priority: 'critical'
    });
  }, [addNotification]);

  return {
    notifySuccess,
    notifyWarning,
    notifyError,
    notifyCritical,
    notifyUserAction,
    notifyPartnerUpdate,
    notifyEnergyTransaction,
    notifySecurityAlert
  };
}
