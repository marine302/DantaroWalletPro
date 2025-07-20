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
    const unsubscribe = notificationManager.subscribe((updatedNotifications) => {
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
  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
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
  const getFilteredNotifications = useCallback(() => {
    return getNotificationsFromManager();
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
  const unreadNotifications = notifications.filter(n => !n.read);
  const criticalNotifications = notifications.filter(n => n.priority === NotificationPriority.CRITICAL && !n.read);

  // Quick notification creators
  const addSystemNotification = useCallback((title: string, message: string) => {
    return addNotification({
      title,
      message,
      channel: NotificationChannel.SYSTEM,
      type: 'info',
      priority: NotificationPriority.LOW
    });
  }, [addNotification]);

  const addSecurityAlert = useCallback((title: string, message: string) => {
    return addNotification({
      title,
      message,
      channel: NotificationChannel.SECURITY,
      type: 'warning',
      priority: NotificationPriority.MEDIUM
    });
  }, [addNotification]);

  const addCriticalAlert = useCallback((title: string, message: string) => {
    return addNotification({
      title,
      message,
      channel: NotificationChannel.SYSTEM,
      type: 'error',
      priority: NotificationPriority.HIGH
    });
  }, [addNotification]);

  const addSecurityBreach = useCallback((title: string, message: string) => {
    return addNotification({
      title,
      message,
      channel: NotificationChannel.SECURITY,
      type: 'error',
      priority: NotificationPriority.CRITICAL
    });
  }, [addNotification]);

  const addUserNotification = useCallback((title: string, message: string) => {
    return addNotification({
      title,
      message,
      channel: NotificationChannel.PARTNER,
      type: 'info',
      priority: NotificationPriority.LOW
    });
  }, [addNotification]);

  const addPartnerUpdate = useCallback((title: string, message: string) => {
    return addNotification({
      title,
      message,
      channel: NotificationChannel.PARTNER,
      type: 'info',
      priority: NotificationPriority.MEDIUM
    });
  }, [addNotification]);

  const addEnergyAlert = useCallback((title: string, message: string) => {
    return addNotification({
      title,
      message,
      channel: NotificationChannel.TRADING,
      type: 'warning',
      priority: NotificationPriority.MEDIUM
    });
  }, [addNotification]);

  const addEmergencyAlert = useCallback((title: string, message: string) => {
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
