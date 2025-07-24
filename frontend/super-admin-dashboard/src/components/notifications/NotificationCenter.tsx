'use client';

import React from 'react';
import { useNotifications } from '@/hooks/useNotifications';
import { Notification, NotificationPriority, NotificationType } from '@/types/notification';

export function NotificationCenter() {
  const {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    clearAll
  } = useNotifications();

  const _getTypeIcon = (type: NotificationType) => {
    const iconMap: Record<NotificationType, string> = {
      info: '📢',
      warning: '⚠️',
      error: '🚨',
      success: '✅'
    };
    return iconMap[type] || '📢';
  };

  const _getPriorityColor = (priority: NotificationPriority) => {
    switch (priority) {
      case NotificationPriority.CRITICAL:
        return 'border-red-500 bg-red-900/20';
      case NotificationPriority.HIGH:
        return 'border-orange-500 bg-orange-900/20';
      case NotificationPriority.MEDIUM:
        return 'border-yellow-500 bg-yellow-900/20';
      case NotificationPriority.LOW:
        return 'border-blue-500 bg-blue-900/20';
      default:
        return 'border-gray-500 bg-gray-900/20';
    }
  };

  const _formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleString('ko-KR');
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-gray-800 rounded-lg shadow-lg">
        {/* Header */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-white">
              알림 센터
            </h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-400">
                읽지 않음: {unreadCount}
              </span>
              <button
                onClick={markAllAsRead}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                모두 읽음으로 표시
              </button>
              <button
                onClick={clearAll}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                모두 삭제
              </button>
            </div>
          </div>
        </div>

        {/* Notifications List */}
        <div className="divide-y divide-gray-700">
          {notifications.length === 0 ? (
            <div className="p-8 text-center text-gray-400">
              <p>새로운 알림이 없습니다.</p>
            </div>
          ) : (
            notifications.map((notification) => (
              <div
                key={notification.id}
                className={`p-4 hover:bg-gray-700/50 transition-colors ${
                  !notification.read ? 'bg-gray-700/30' : ''
                }`}
              >
                <div className={`border-l-4 pl-4 ${_getPriorityColor(notification.priority)}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-lg">
                          {_getTypeIcon(notification.type)}
                        </span>
                        <h3 className="font-semibold text-white">
                          {notification.title}
                        </h3>
                        <span className="text-xs px-2 py-1 bg-gray-600 text-gray-300 rounded">
                          {notification.priority}
                        </span>
                        <span className="text-xs px-2 py-1 bg-gray-600 text-gray-300 rounded">
                          {notification.channel}
                        </span>
                      </div>

                      <p className="text-gray-300 mb-2">
                        {notification.message}
                      </p>

                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-400">
                          {_formatTimestamp(notification.timestamp)}
                        </span>

                        <div className="flex items-center space-x-2">
                          {!notification.read && (
                            <button
                              onClick={() => markAsRead(notification.id)}
                              className="text-xs px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                            >
                              읽음으로 표시
                            </button>
                          )}
                          <button
                            onClick={() => deleteNotification(notification.id)}
                            className="text-xs px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                          >
                            삭제
                          </button>
                        </div>
                      </div>

                      {/* Actions */}
                      {notification.actions && notification.actions.length > 0 && (
                        <div className="mt-3 flex space-x-2">
                          {notification.actions.map((action, index) => (
                            <button
                              key={index}
                              onClick={action.action}
                              className="text-xs px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                            >
                              {action.label}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default NotificationCenter;
