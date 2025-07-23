'use client';

import React, { useState } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { BellIcon, CheckIcon, TrashIcon, Cog6ToothIcon } from '@heroicons/react/24/outline';
import { useNotifications } from '@/hooks/useNotifications';
import { Notification, NotificationPriority } from '@/types/notification';
import { cn } from '@/lib/utils';

export function NotificationBell() {
  const {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    deleteNotification
  } = useNotifications();

  const [isOpen, setIsOpen] = useState(false);
  const _recentNotifications = notifications.slice(0, 5);

  const _getPriorityColor = (priority: NotificationPriority) => {
    switch (priority) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const _getTypeIcon = (type: string) => {
    const iconMap: Record<string, string> = {
      system: '⚙️',
      security: '🔒',
      transaction: '💰',
      partner: '🤝',
      user: '👤',
      energy: '⚡',
      audit: '📋',
      maintenance: '🔧'
    };
    return iconMap[type] || '📢';
  };

  const _formatTimestamp = (timestamp: string) => {
    const _date = new Date(timestamp);
    const _now = new Date();
    const _diffMs = now.getTime() - date.getTime();
    const _diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const _diffMinutes = Math.floor(diffMs / (1000 * 60));

    if (diffMinutes < 1) return '방금 전';
    if (diffMinutes < 60) return `${diffMinutes}분 전`;
    if (diffHours < 24) return `${diffHours}시간 전`;
    return date.toLocaleDateString('ko-KR');
  };

  const _handleMarkAsRead = (e: React.MouseEvent, notificationId: string) => {
    e.stopPropagation();
    markAsRead(notificationId);
  };

  const _handleDelete = (e: React.MouseEvent, notificationId: string) => {
    e.stopPropagation();
    deleteNotification(notificationId);
  };

  return (
    <Menu as="div" className="relative">
      <Menu.Button className="relative p-2 text-gray-400 hover:text-gray-300 focus:outline-none">
        <BellIcon className="h-6 w-6" aria-hidden="true" />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </Menu.Button>

      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className="absolute right-0 z-50 mt-2 w-80 origin-top-right rounded-lg bg-gray-800 shadow-lg ring-1 ring-gray-700 focus:outline-none">
          <div className="p-4">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-white">
                알림 ({unreadCount}개 읽지 않음)
              </h3>
              <div className="flex space-x-2">
                {unreadCount > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="text-xs text-blue-400 hover:text-blue-300"
                  >
                    모두 읽음
                  </button>
                )}
                <Cog6ToothIcon className="w-4 h-4 text-gray-400 hover:text-gray-300 cursor-pointer" />
              </div>
            </div>

            {/* Notifications */}
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {recentNotifications.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <BellIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">새로운 알림이 없습니다</p>
                </div>
              ) : (
                recentNotifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={cn(
                      'relative p-3 rounded-lg border border-gray-700 cursor-pointer transition-colors',
                      notification.read
                        ? 'bg-gray-900 opacity-75'
                        : 'bg-gray-800 hover:bg-gray-750'
                    )}
                    onClick={() => !notification.read && markAsRead(notification.id)}
                  >
                    {/* Priority indicator */}
                    <div className={cn(
                      'absolute top-2 left-2 w-2 h-2 rounded-full',
                      getPriorityColor(notification.priority)
                    )} />

                    {/* Content */}
                    <div className="ml-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <span className="text-sm">
                              {getTypeIcon(notification.type)}
                            </span>
                            <p className={cn(
                              'text-sm font-medium truncate',
                              notification.read ? 'text-gray-400' : 'text-white'
                            )}>
                              {notification.title}
                            </p>
                          </div>
                          <p className={cn(
                            'text-xs mt-1 line-clamp-2',
                            notification.read ? 'text-gray-500' : 'text-gray-300'
                          )}>
                            {notification.message}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            {notification.timestamp.toLocaleString('ko-KR')}
                          </p>
                        </div>

                        {/* Actions */}
                        <div className="flex space-x-1 ml-2">
                          {!notification.read && (
                            <button
                              onClick={(e) => handleMarkAsRead(e, notification.id)}
                              className="p-1 text-gray-400 hover:text-green-400"
                              title="읽음으로 표시"
                            >
                              <CheckIcon className="w-3 h-3" />
                            </button>
                          )}
                          <button
                            onClick={(e) => handleDelete(e, notification.id)}
                            className="p-1 text-gray-400 hover:text-red-400"
                            title="삭제"
                          >
                            <TrashIcon className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Footer */}
            {notifications.length > 5 && (
              <div className="mt-4 pt-3 border-t border-gray-700 text-center">
                <button className="text-sm text-blue-400 hover:text-blue-300">
                  모든 알림 보기
                </button>
              </div>
            )}
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  );
}
