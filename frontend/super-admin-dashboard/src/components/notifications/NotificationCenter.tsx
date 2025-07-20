'use client';

import React, { useState } from 'react';
import { useNotifications } from '@/hooks/useNotifications';
import { Notification, NotificationPriority, NotificationType } from '@/types/notification';
import { BasePage } from '@/components/ui/BasePage';
import { Section } from '@/components/ui/DarkThemeComponents';
import { PermissionGuard } from '@/components/auth/PermissionGuard';
import { 
  CheckIcon, 
  TrashIcon, 
  FunnelIcon,
  BellIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon 
} from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';

export function NotificationCenter() {
  const { 
    notifications, 
    unreadCount, 
    stats,
    markAsRead, 
    markAllAsRead,
    deleteNotification,
    clearAll,
    getNotifications
  } = useNotifications();

  const [filters, setFilters] = useState({
    type: '' as NotificationType | '',
    priority: '' as NotificationPriority | '',
    unreadOnly: false
  });

  const [selectedNotifications, setSelectedNotifications] = useState<string[]>([]);

  // Apply filters
  const filteredNotifications = getNotifications({
    type: filters.type || undefined,
    priority: filters.priority || undefined,
    unreadOnly: filters.unreadOnly
  });

  const getPriorityColor = (priority: NotificationPriority) => {
    switch (priority) {
      case 'critical': return 'text-red-400 bg-red-900/20';
      case 'high': return 'text-orange-400 bg-orange-900/20';
      case 'medium': return 'text-yellow-400 bg-yellow-900/20';
      case 'low': return 'text-blue-400 bg-blue-900/20';
      default: return 'text-gray-400 bg-gray-900/20';
    }
  };

  const getPriorityIcon = (priority: NotificationPriority) => {
    switch (priority) {
      case 'critical': return <ExclamationTriangleIcon className="w-4 h-4" />;
      case 'high': return <ExclamationTriangleIcon className="w-4 h-4" />;
      case 'medium': return <InformationCircleIcon className="w-4 h-4" />;
      case 'low': return <InformationCircleIcon className="w-4 h-4" />;
      default: return <BellIcon className="w-4 h-4" />;
    }
  };

  const getTypeIcon = (type: NotificationType) => {
    const iconMap: Record<NotificationType, string> = {
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

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('ko-KR');
  };

  const handleSelectNotification = (notificationId: string) => {
    setSelectedNotifications(prev => 
      prev.includes(notificationId)
        ? prev.filter(id => id !== notificationId)
        : [...prev, notificationId]
    );
  };

  const handleSelectAll = () => {
    if (selectedNotifications.length === filteredNotifications.length) {
      setSelectedNotifications([]);
    } else {
      setSelectedNotifications(filteredNotifications.map(n => n.id));
    }
  };

  const handleBulkMarkAsRead = () => {
    selectedNotifications.forEach(id => markAsRead(id));
    setSelectedNotifications([]);
  };

  const handleBulkDelete = () => {
    if (confirm(`선택된 ${selectedNotifications.length}개의 알림을 삭제하시겠습니까?`)) {
      selectedNotifications.forEach(id => deleteNotification(id));
      setSelectedNotifications([]);
    }
  };

  return (
    <PermissionGuard permission="system.view_logs">
      <BasePage title="알림 센터" description="시스템 알림을 확인하고 관리합니다">
        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-gray-800 p-4 rounded-lg">
            <div className="flex items-center">
              <BellIcon className="w-8 h-8 text-blue-400" />
              <div className="ml-3">
                <p className="text-sm text-gray-400">전체 알림</p>
                <p className="text-xl font-semibold text-white">{stats?.total || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-800 p-4 rounded-lg">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-sm">{stats?.unread || 0}</span>
              </div>
              <div className="ml-3">
                <p className="text-sm text-gray-400">읽지 않음</p>
                <p className="text-xl font-semibold text-white">{stats?.unread || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-gray-800 p-4 rounded-lg">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="w-8 h-8 text-red-400" />
              <div className="ml-3">
                <p className="text-sm text-gray-400">긴급</p>
                <p className="text-xl font-semibold text-white">
                  {stats?.byPriority.critical || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-800 p-4 rounded-lg">
            <div className="flex items-center">
              <InformationCircleIcon className="w-8 h-8 text-green-400" />
              <div className="ml-3">
                <p className="text-sm text-gray-400">최근 1시간</p>
                <p className="text-xl font-semibold text-white">
                  {stats?.recentCount || 0}
                </p>
              </div>
            </div>
          </div>
        </div>

        <Section title="알림 목록">
          {/* Filters and Actions */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
            <div className="flex flex-wrap gap-3">
              <select
                value={filters.type}
                onChange={(e) => setFilters(f => ({ ...f, type: e.target.value as NotificationType }))}
                className="px-3 py-1 bg-gray-700 border border-gray-600 rounded text-white text-sm"
              >
                <option value="">모든 유형</option>
                <option value="system">시스템</option>
                <option value="security">보안</option>
                <option value="transaction">거래</option>
                <option value="partner">파트너</option>
                <option value="user">사용자</option>
                <option value="energy">에너지</option>
                <option value="audit">감사</option>
                <option value="maintenance">유지보수</option>
              </select>

              <select
                value={filters.priority}
                onChange={(e) => setFilters(f => ({ ...f, priority: e.target.value as NotificationPriority }))}
                className="px-3 py-1 bg-gray-700 border border-gray-600 rounded text-white text-sm"
              >
                <option value="">모든 우선순위</option>
                <option value="critical">긴급</option>
                <option value="high">높음</option>
                <option value="medium">보통</option>
                <option value="low">낮음</option>
              </select>

              <label className="flex items-center space-x-2 text-sm text-white">
                <input
                  type="checkbox"
                  checked={filters.unreadOnly}
                  onChange={(e) => setFilters(f => ({ ...f, unreadOnly: e.target.checked }))}
                  className="rounded"
                />
                <span>읽지 않음만</span>
              </label>
            </div>

            <div className="flex gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                >
                  모두 읽음
                </button>
              )}
              {notifications.length > 0 && (
                <button
                  onClick={() => confirm('모든 알림을 삭제하시겠습니까?') && clearAll()}
                  className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
                >
                  모두 삭제
                </button>
              )}
            </div>
          </div>

          {/* Bulk Actions */}
          {selectedNotifications.length > 0 && (
            <div className="bg-gray-700 p-3 rounded-lg mb-4 flex items-center justify-between">
              <span className="text-white text-sm">
                {selectedNotifications.length}개 선택됨
              </span>
              <div className="flex gap-2">
                <button
                  onClick={handleBulkMarkAsRead}
                  className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                >
                  읽음 처리
                </button>
                <button
                  onClick={handleBulkDelete}
                  className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
                >
                  삭제
                </button>
              </div>
            </div>
          )}

          {/* Notifications List */}
          <div className="space-y-3">
            {filteredNotifications.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <BellIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>표시할 알림이 없습니다.</p>
              </div>
            ) : (
              <>
                {/* Select All */}
                <div className="flex items-center space-x-3 pb-2 border-b border-gray-700">
                  <input
                    type="checkbox"
                    checked={selectedNotifications.length === filteredNotifications.length}
                    onChange={handleSelectAll}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-400">전체 선택</span>
                </div>

                {filteredNotifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={cn(
                      'flex items-start space-x-3 p-4 rounded-lg border transition-colors',
                      notification.isRead 
                        ? 'bg-gray-900 border-gray-700 opacity-75' 
                        : 'bg-gray-800 border-gray-600',
                      selectedNotifications.includes(notification.id) && 'ring-2 ring-blue-500'
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={selectedNotifications.includes(notification.id)}
                      onChange={() => handleSelectNotification(notification.id)}
                      className="mt-1"
                    />

                    <div className={cn(
                      'flex items-center justify-center w-8 h-8 rounded-full text-sm',
                      getPriorityColor(notification.priority)
                    )}>
                      {getPriorityIcon(notification.priority)}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-lg">{getTypeIcon(notification.type)}</span>
                        <h4 className={cn(
                          'font-medium truncate',
                          notification.isRead ? 'text-gray-400' : 'text-white'
                        )}>
                          {notification.title}
                        </h4>
                        <span className={cn(
                          'px-2 py-1 text-xs rounded-full',
                          getPriorityColor(notification.priority)
                        )}>
                          {notification.priority}
                        </span>
                      </div>
                      <p className={cn(
                        'text-sm mb-2',
                        notification.isRead ? 'text-gray-500' : 'text-gray-300'
                      )}>
                        {notification.message}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatTimestamp(notification.timestamp)}
                      </p>
                    </div>

                    <div className="flex space-x-1">
                      {!notification.isRead && (
                        <button
                          onClick={() => markAsRead(notification.id)}
                          className="p-2 text-gray-400 hover:text-green-400"
                          title="읽음으로 표시"
                        >
                          <CheckIcon className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => deleteNotification(notification.id)}
                        className="p-2 text-gray-400 hover:text-red-400"
                        title="삭제"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        </Section>
      </BasePage>
    </PermissionGuard>
  );
}
