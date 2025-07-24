'use client';

import React, { useState, useEffect } from 'react';
import { _notificationManager } from '@/lib/notification-manager';
import { useNotifications } from '@/hooks/useNotifications';
import {
  Notification,
  NotificationPriority,
  NotificationChannel,
  NotificationFilter
} from '@/types/notification';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface NotificationHistoryProps {
  onClose?: () => void;
}

export const NotificationHistory: React.FC<NotificationHistoryProps> = ({ onClose }) => {
  const [history, setHistory] = useState<Notification[]>([]);
  const [filters, setFilters] = useState<NotificationFilter>({
    priorities: Object.values(NotificationPriority),
    channels: Object.values(NotificationChannel),
    dateRange: null,
    readStatus: 'all',
    searchQuery: ''
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);

  useEffect(() => {
    const _unsubscribe = _notificationManager.subscribeToHistory((newHistory) => {
      setHistory(newHistory);
    });

    // 초기 히스토리 로드
    setHistory(_notificationManager.getNotificationHistory());

    return _unsubscribe;
  }, []);

  useEffect(() => {
    _notificationManager.updateFilters(filters);
  }, [filters]);

  const _handleFilterChange = (key: keyof NotificationFilter, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1); // 필터 변경시 첫 페이지로
  };

  const _handleDateRangeChange = (type: 'start' | 'end', date: string) => {
    const _newDateRange = filters.dateRange || { start: new Date(), end: new Date() };
    if (type === 'start') {
      _newDateRange.start = new Date(date);
    } else {
      _newDateRange.end = new Date(date);
    }
    _handleFilterChange('dateRange', _newDateRange);
  };

  const _clearDateFilter = () => {
    _handleFilterChange('dateRange', null);
  };

  const _getPriorityColor = (priority: NotificationPriority) => {
    switch (priority) {
      case NotificationPriority.CRITICAL:
        return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-300';
      case NotificationPriority.HIGH:
        return 'text-orange-600 bg-orange-100 dark:bg-orange-900 dark:text-orange-300';
      case NotificationPriority.MEDIUM:
        return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-300';
      case NotificationPriority.LOW:
        return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-300';
      default:
        return 'text-gray-600 bg-gray-100 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  const _getChannelIcon = (channel: NotificationChannel) => {
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

  const _formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(date));
  };

  // 페이지네이션 계산
  const _totalItems = history.length;
  const _totalPages = Math.ceil(_totalItems / itemsPerPage);
  const _startIndex = (currentPage - 1) * itemsPerPage;
  const _endIndex = _startIndex + itemsPerPage;
  const _currentItems = history.slice(_startIndex, _endIndex);

  const _exportToCSV = () => {
    const _csvData = history.map(notification => ({
      ID: notification.id,
      Title: notification.title,
      Message: notification.message,
      Priority: notification.priority,
      Channel: notification.channel,
      Timestamp: _formatDate(notification.timestamp),
      Read: notification.read ? 'Yes' : 'No'
    }));

    const _headers = Object.keys(_csvData[0] || {});
    const _csvContent = [
      _headers.join(','),
      ..._csvData.map(row => _headers.map(header => `"${row[header as keyof typeof row]}"`).join(','))
    ].join('\n');

    const _blob = new Blob([_csvContent], { type: 'text/csv' });
    const _url = window.URL.createObjectURL(_blob);
    const _a = document.createElement('a');
    _a.href = _url;
    _a.download = `notification-history-${new Date().toISOString().split('T')[0]}.csv`;
    _a.click();
    window.URL.revokeObjectURL(_url);
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          알림 히스토리
        </h2>
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            onClick={_exportToCSV}
            disabled={history.length === 0}
          >
            📊 CSV 내보내기
          </Button>
          {onClose && (
            <Button
              variant="outline"
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </Button>
          )}
        </div>
      </div>

      {/* 필터 섹션 */}
      <Card className="p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          필터
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* 검색 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              검색
            </label>
            <input
              type="text"
              placeholder="제목 또는 메시지 검색..."
              value={filters.searchQuery}
              onChange={(e) => _handleFilterChange('searchQuery', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
          </div>

          {/* 읽음 상태 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              읽음 상태
            </label>
            <select
              value={filters.readStatus}
              onChange={(e) => _handleFilterChange('readStatus', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            >
              <option value="all">전체</option>
              <option value="read">읽음</option>
              <option value="unread">읽지 않음</option>
            </select>
          </div>

          {/* 우선순위 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              우선순위
            </label>
            <select
              multiple
              value={filters.priorities}
              onChange={(e) => {
                const _selected = Array.from(e.target.selectedOptions, option => option.value as NotificationPriority);
                _handleFilterChange('priorities', _selected);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              size={4}
            >
              {Object.values(NotificationPriority).map(priority => (
                <option key={priority} value={priority} className="capitalize">
                  {priority}
                </option>
              ))}
            </select>
          </div>

          {/* 채널 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              채널
            </label>
            <select
              multiple
              value={filters.channels}
              onChange={(e) => {
                const _selected = Array.from(e.target.selectedOptions, option => option.value as NotificationChannel);
                _handleFilterChange('channels', _selected);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              size={5}
            >
              {Object.values(NotificationChannel).map(channel => (
                <option key={channel} value={channel} className="capitalize">
                  {_getChannelIcon(channel)} {channel.replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 날짜 범위 */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              시작 날짜
            </label>
            <input
              type="date"
              value={filters.dateRange?.start ? filters.dateRange.start.toISOString().split('T')[0] : ''}
              onChange={(e) => _handleDateRangeChange('start', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              종료 날짜
            </label>
            <input
              type="date"
              value={filters.dateRange?.end ? filters.dateRange.end.toISOString().split('T')[0] : ''}
              onChange={(e) => _handleDateRangeChange('end', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
          </div>

          <div>
            <Button
              variant="outline"
              onClick={_clearDateFilter}
              disabled={!filters.dateRange}
              className="w-full"
            >
              날짜 필터 지우기
            </Button>
          </div>
        </div>
      </Card>

      {/* 히스토리 목록 */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            알림 히스토리 ({_totalItems}개)
          </h3>

          {/* 페이지네이션 정보 */}
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {_startIndex + 1}-{Math.min(_endIndex, _totalItems)} / {_totalItems}
          </div>
        </div>

        {_currentItems.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            조건에 맞는 알림이 없습니다.
          </div>
        ) : (
          <div className="space-y-4">
            {_currentItems.map((notification) => (
              <div
                key={notification.id}
                className={`border rounded-lg p-4 transition-colors ${
                  notification.read
                    ? 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                    : 'bg-white dark:bg-gray-900 border-blue-200 dark:border-blue-800'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className="text-lg">{_getChannelIcon(notification.channel)}</span>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${_getPriorityColor(notification.priority)}`}>
                        {notification.priority.toUpperCase()}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {_formatDate(notification.timestamp)}
                      </span>
                      {!notification.read && (
                        <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                      )}
                    </div>

                    <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                      {notification.title}
                    </h4>

                    <p className="text-gray-600 dark:text-gray-300 text-sm">
                      {notification.message}
                    </p>
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    {!notification.read && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => _notificationManager.markAsRead(notification.id)}
                        className="text-xs"
                      >
                        읽음 처리
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 페이지네이션 */}
        {_totalPages > 1 && (
          <div className="flex items-center justify-center space-x-2 mt-6">
            <Button
              variant="outline"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(prev => prev - 1)}
            >
              이전
            </Button>

            <div className="flex space-x-1">
              {[...Array(_totalPages)].map((_, index) => {
                const _page = index + 1;
                const _isCurrentPage = _page === currentPage;
                const _showPage = _page === 1 || _page === _totalPages || (_page >= currentPage - 2 && _page <= currentPage + 2);

                if (!_showPage) {
                  if (_page === currentPage - 3 || _page === currentPage + 3) {
                    return <span key={_page} className="px-2 text-gray-400">...</span>;
                  }
                  return null;
                }

                return (
                  <Button
                    key={_page}
                    variant={_isCurrentPage ? "default" : "outline"}
                    size="sm"
                    onClick={() => setCurrentPage(_page)}
                    className={_isCurrentPage ? "bg-blue-600 text-white" : ""}
                  >
                    {_page}
                  </Button>
                );
              })}
            </div>

            <Button
              variant="outline"
              disabled={currentPage === _totalPages}
              onClick={() => setCurrentPage(prev => prev + 1)}
            >
              다음
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};
