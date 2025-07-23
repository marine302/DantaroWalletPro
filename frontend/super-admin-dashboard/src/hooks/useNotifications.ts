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
  NotificationChannel,
  NotificationSettings,
  NotificationStats
} from '@/types/notification';

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [stats, setStats] = useState<NotificationStats | null>(null);

  // Update state when notifications change
  useEffect(() => {
    const _unsubscribe = notificationManager.subscribe((updatedNotifications) => {
      setNotifications(updatedNotifications);
      setStats(notificationManager.getStats());
    });

    // Initial load
    setNotifications(getNotificationsFromManager());
    setSettings(notificationManager.getSettings());
    setStats(notificationManager.getStats());

    return unsubscribe;
  }, []);

  // Add notification
  const _addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    return addNotificationToManager(notification);
  }, []);

  // Mark as read
  const _markAsRead = useCallback((notificationId: string) => {
    markNotificationAsRead(notificationId);
  }, []);

  // Mark all as read
  const _markAllAsRead = useCallback(() => {
    notificationManager.markAllAsRead();
  }, []);

  // Delete notification
  const _deleteNotification = useCallback((notificationId: string) => {
    notificationManager.deleteNotification(notificationId);
  }, []);

  // Clear all notifications
  const _clearAll = useCallback(() => {
    notificationManager.clearAll();
  }, []);

  // Get filtered notifications
  const _getFilteredNotifications = useCallback(() => {
    return getNotificationsFromManager();
  }, []);

  // Update settings
  const _updateSettings = useCallback((newSettings: Partial<NotificationSettings>) => {
    notificationManager.updateSettings(newSettings);
    setSettings(notificationManager.getSettings());
  }, []);

  // Request browser notification permission
  const _requestPermission = useCallback(async () => {
    return await notificationManager.requestPermission();
  }, []);

  // Convenience getters
  const _unreadCount = stats?.unread || 0;
  const _unreadNotifications = notifications.filter(n => !n.read);
  const _criticalNotifications = notifications.filter(n => n.priority === NotificationPriority.CRITICAL && !n.read);

  // Quick notification creators
  const _addSystemNotification = useCallback((title: string, message: string) => {
    return addNotification({
      title,
      message,
      channel: NotificationChannel.SYSTEM,
      type: 'info',
      priority: NotificationPriority.LOW
    });
  }, [addNotification]);

  const _addSecurityAlert = useCallback((title: string, message: string) => {
    return addNotification({
      title,
      message,
      channel: NotificationChannel.SECURITY,
      type: 'warning',
      priority: NotificationPriority.MEDIUM
    });
  }, [addNotification]);

  const _addCriticalAlert = useCallback((title: string, message: string) => {
    return addNotification({
      title,
      message,
      channel: NotificationChannel.SYSTEM,
      type: 'error',
      priority: NotificationPriority.HIGH
    });
  }, [addNotification]);

  const _addSecurityBreach = useCallback((title: string, message: string) => {
    return addNotification({
      title,
      message,
      channel: NotificationChannel.SECURITY,
      type: 'error',
      priority: NotificationPriority.CRITICAL
    });
  }, [addNotification]);

  const _addUserNotification = useCallback((title: string, message: string) => {
    return addNotification({
      title,
      message,
      channel: NotificationChannel.PARTNER,
      type: 'info',
      priority: NotificationPriority.LOW
    });
  }, [addNotification]);

  const _addPartnerUpdate = useCallback((title: string, message: string) => {
    return addNotification({
      title,
      message,
      channel: NotificationChannel.PARTNER,
      type: 'info',
      priority: NotificationPriority.MEDIUM
    });
  }, [addNotification]);

  const _addEnergyAlert = useCallback((title: string, message: string) => {
    return addNotification({
      title,
      message,
      channel: NotificationChannel.TRADING,
      type: 'warning',
      priority: NotificationPriority.MEDIUM
    });
  }, [addNotification]);

  const _addEmergencyAlert = useCallback((title: string, message: string) => {
    return addNotification({
      title,
      message,
      channel: NotificationChannel.SECURITY,
      type: 'error',
      priority: NotificationPriority.CRITICAL
    });
  }, [addNotification]);

  return {
    // Data
    notifications,
    unreadNotifications,
    criticalNotifications,
    settings,
    stats,

    // Counts
    unreadCount,

    // Actions
    addNotification,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    clearAll,
    getFilteredNotifications,
    updateSettings,
    requestPermission,

    // Quick creators
    addSystemNotification,
    addSecurityAlert,
    addCriticalAlert,
    addSecurityBreach,
    addUserNotification,
    addPartnerUpdate,
    addEnergyAlert,
    addEmergencyAlert
  };
}
