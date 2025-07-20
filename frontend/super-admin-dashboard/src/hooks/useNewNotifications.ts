'use client';

import { useState, useEffect, useCallback } from 'react';
import { notificationManager } from '@/lib/notification-manager';
import { INotification, NotificationPriority, NotificationChannel } from '@/types/notification';

export function useNewNotifications() {
  const [notifications, setNotifications] = useState<INotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    // 초기 데이터 로드
    setNotifications(notificationManager.getActiveNotifications());
    setUnreadCount(notificationManager.getUnreadCount());

    // 구독
    const unsubscribe = notificationManager.subscribe((updatedNotifications) => {
      setNotifications(updatedNotifications);
      setUnreadCount(notificationManager.getUnreadCount());
    });

    return unsubscribe;
  }, []);

  const addNotification = useCallback((notification: Omit<INotification, 'id' | 'timestamp' | 'read'>) => {
    return notificationManager.addNotification(notification);
  }, []);

  const markAsRead = useCallback((id: string) => {
    notificationManager.markAsRead(id);
  }, []);

  const markAllAsRead = useCallback(() => {
    notificationManager.markAllAsRead();
  }, []);

  const removeNotification = useCallback((id: string) => {
    notificationManager.removeNotification(id);
  }, []);

  const clearAll = useCallback(() => {
    notificationManager.clearAll();
  }, []);

  return {
    notifications,
    unreadCount,
    addNotification,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAll
  };
}
