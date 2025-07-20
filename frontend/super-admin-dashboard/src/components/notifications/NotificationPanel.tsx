'use client';

import React, { useState } from 'react';
import { useNewNotifications } from '@/hooks/useNewNotifications';
import { NotificationPriority, NotificationChannel } from '@/types/notification';
import { NotificationSettingsComponent } from './NotificationSettings';
import { NotificationHistory } from './NotificationHistory';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface NotificationPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

type ViewMode = 'notifications' | 'settings' | 'history';

export const NotificationPanel: React.FC<NotificationPanelProps> = ({
  isOpen,
  onClose
}) => {
  const { 
    notifications, 
    unreadCount, 
    markAsRead, 
    markAllAsRead,
    removeNotification,
    clearAll 
  } = useNewNotifications();

  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const [currentView, setCurrentView] = useState<ViewMode>('notifications');

  if (!isOpen) return null;

  const filteredNotifications = filter === 'all' 
    ? notifications 
    : notifications.filter(n => !n.read);

  const getPriorityColor = (priority: NotificationPriority) => {
    switch (priority) {
      case NotificationPriority.CRITICAL:
        return 'border-l-red-500 bg-red-50 dark:bg-red-900/20';
      case NotificationPriority.HIGH:
        return 'border-l-orange-500 bg-orange-50 dark:bg-orange-900/20';
      case NotificationPriority.MEDIUM:
        return 'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-900/20';
      case NotificationPriority.LOW:
        return 'border-l-green-500 bg-green-50 dark:bg-green-900/20';
      default:
        return 'border-l-gray-500 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  const getChannelIcon = (channel: NotificationChannel) => {
    switch (channel) {
      case NotificationChannel.SYSTEM:
        return '⚙️';
      case NotificationChannel.SECURITY:
        return '🔒';
      case NotificationChannel.TRADING:
        return '💹';
      case NotificationChannel.PARTNER:
        return '🤝';
      case NotificationChannel.COMPLIANCE:
        return '📋';
      default:
        return '📢';
    }
  };

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - new Date(date).getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '방금 전';
    if (minutes < 60) return `${minutes}분 전`;
    if (hours < 24) return `${hours}시간 전`;
    return `${days}일 전`;
  };

  const renderNotificationsList = () => (
    <>
      {/* 필터 및 액션 */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex space-x-2">
          <Button
            variant={filter === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('all')}
          >
            전체
          </Button>
          <Button
            variant={filter === 'unread' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('unread')}
          >
            읽지 않음
          </Button>
        </div>
        
        <div className="flex space-x-2">
          {unreadCount > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={markAllAsRead}
            >
              모두 읽음
            </Button>
          )}
          {notifications.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={clearAll}
            >
              모두 지우기
            </Button>
          )}
        </div>
      </div>

      {/* 알림 목록 */}
      <div className="flex-1 overflow-y-auto">
        {filteredNotifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
            <div className="text-4xl mb-4">🔔</div>
            <p className="text-center">
              {filter === 'unread' ? '읽지 않은 알림이 없습니다.' : '알림이 없습니다.'}
            </p>
          </div>
        ) : (
          <div className="p-4 space-y-3">
            {filteredNotifications.map((notification) => (
              <div
                key={notification.id}
                className={`border-l-4 rounded-lg p-4 transition-colors cursor-pointer ${
                  getPriorityColor(notification.priority)
                } ${
                  !notification.read 
                    ? 'ring-2 ring-blue-500 ring-opacity-20' 
                    : 'opacity-75'
                }`}
                onClick={() => !notification.read && markAsRead(notification.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    <span className="text-lg mt-1">
                      {getChannelIcon(notification.channel)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <h4 className="font-medium text-gray-900 dark:text-white text-sm truncate">
                          {notification.title}
                        </h4>
                        {!notification.read && (
                          <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0"></span>
                        )}
                      </div>
                      <p className="text-gray-600 dark:text-gray-300 text-sm line-clamp-2">
                        {notification.message}
                      </p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {formatTime(notification.timestamp)}
                        </span>
                        <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          {notification.priority}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeNotification(notification.id);
                    }}
                    className="ml-2 p-1 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );

  const renderContent = () => {
    switch (currentView) {
      case 'settings':
        return <NotificationSettingsComponent onClose={() => setCurrentView('notifications')} />;
      case 'history':
        return <NotificationHistory onClose={() => setCurrentView('notifications')} />;
      default:
        return renderNotificationsList();
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* 배경 오버레이 */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* 알림 패널 */}
      <div className={`absolute right-0 top-0 h-full bg-white dark:bg-gray-900 shadow-xl transform transition-transform ${
        currentView === 'notifications' ? 'w-full max-w-md' : 'w-full max-w-4xl'
      }`}>
        <div className="flex flex-col h-full">
          {/* 헤더 */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-3">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {currentView === 'notifications' && '알림'}
                {currentView === 'settings' && '알림 설정'}
                {currentView === 'history' && '알림 히스토리'}
              </h2>
              {currentView === 'notifications' && unreadCount > 0 && (
                <span className="px-2 py-1 text-xs font-medium text-white bg-red-500 rounded-full">
                  {unreadCount}
                </span>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              {currentView === 'notifications' && (
                <>
                  <button
                    onClick={() => setCurrentView('history')}
                    className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
                    title="히스토리 보기"
                  >
                    📋
                  </button>
                  <button
                    onClick={() => setCurrentView('settings')}
                    className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
                    title="설정"
                  >
                    ⚙️
                  </button>
                </>
              )}
              <button
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                ✕
              </button>
            </div>
          </div>

          {/* 컨텐츠 */}
          {currentView === 'notifications' ? (
            renderContent()
          ) : (
            <div className="flex-1 overflow-y-auto">
              {renderContent()}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
