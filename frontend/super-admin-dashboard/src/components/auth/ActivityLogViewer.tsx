'use client';

import React, { useState, useEffect } from 'react';
import { ActivityLog, getRecentActivities, getUserActivities } from '@/lib/activity-logger';
import { useAuth } from '@/contexts/AuthContext';
import { PermissionGuard } from '@/components/auth/PermissionGuard';

interface ActivityLogViewerProps {
  userId?: string;
  limit?: number;
  showFilters?: boolean;
}

export function ActivityLogViewer({
  userId,
  limit = 20,
  showFilters = true
}: ActivityLogViewerProps) {
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    action: '',
    resource: '',
    dateRange: '7d'
  });
  const { user } = useAuth();

  useEffect(() => {
    _loadLogs();
  }, [userId, limit, filters]);

  const _loadLogs = () => {
    setLoading(true);
    try {
      const _activities = userId
        ? getUserActivities(userId, limit)
        : getRecentActivities(limit);

      // Apply filters
      let _filteredLogs = _activities;

      if (filters.action) {
        _filteredLogs = _filteredLogs.filter(log => log.action === filters.action);
      }

      if (filters.resource) {
        _filteredLogs = _filteredLogs.filter(log => log.resource === filters.resource);
      }

      if (filters.dateRange) {
        const _now = new Date();
        const _daysAgo = parseInt(filters.dateRange);
        const _cutoffDate = new Date(_now.getTime() - (_daysAgo * 24 * 60 * 60 * 1000));
        _filteredLogs = _filteredLogs.filter(log =>
          new Date(log.timestamp) >= _cutoffDate
        );
      }

      setLogs(_filteredLogs);
    } catch (error) {
      console.error('Failed to load activity logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const _formatTimestamp = (timestamp: string) => {
    const _date = new Date(timestamp);
    const _now = new Date();
    const _diffMs = _now.getTime() - _date.getTime();
    const _diffHours = Math.floor(_diffMs / (1000 * 60 * 60));
    const _diffDays = Math.floor(_diffMs / (1000 * 60 * 60 * 24));

    if (_diffHours < 1) {
      const _diffMinutes = Math.floor(_diffMs / (1000 * 60));
      return `${_diffMinutes}분 전`;
    } else if (_diffHours < 24) {
      return `${_diffHours}시간 전`;
    } else if (_diffDays < 7) {
      return `${_diffDays}일 전`;
    } else {
      return _date.toLocaleDateString('ko-KR');
    }
  };

  const _getActivityIcon = (action: string) => {
    const iconMap: Record<string, string> = {
      login: '🔑',
      logout: '🚪',
      create: '➕',
      update: '✏️',
      delete: '🗑️',
      view: '👁️',
      export: '📁',
      approve: '✅',
      reject: '❌',
      suspend: '⏸️',
      activate: '▶️'
    };
    return iconMap[action] || '📝';
  };

  const _getActivityColor = (action: string) => {
    const colorMap: Record<string, string> = {
      login: 'bg-green-600',
      logout: 'bg-gray-600',
      create: 'bg-blue-600',
      update: 'bg-yellow-600',
      delete: 'bg-red-600',
      view: 'bg-indigo-600',
      export: 'bg-purple-600',
      approve: 'bg-green-600',
      reject: 'bg-red-600',
      suspend: 'bg-orange-600',
      activate: 'bg-green-600'
    };
    return colorMap[action] || 'bg-gray-600';
  };

  const _formatActivityMessage = (log: ActivityLog) => {
    const actionMap: Record<string, string> = {
      login: '로그인',
      logout: '로그아웃',
      create: '생성',
      update: '수정',
      delete: '삭제',
      view: '조회',
      export: '내보내기',
      approve: '승인',
      reject: '거부',
      suspend: '정지',
      activate: '활성화'
    };

    const resourceMap: Record<string, string> = {
      user: '사용자',
      partner: '파트너',
      energy_transaction: '에너지 거래',
      fee_setting: '수수료 설정',
      system_setting: '시스템 설정',
      audit_log: '감사 로그',
      dashboard: '대시보드'
    };

    const _action = actionMap[log.action] || log.action;
    const _resource = resourceMap[log.resource] || log.resource;

    return `${_resource} ${_action}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <PermissionGuard permission="system.view_logs">
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold text-white">
            {userId ? '사용자 활동 로그' : '최근 활동'}
          </h3>
          <button
            onClick={_loadLogs}
            className="text-blue-400 hover:text-blue-300 text-sm"
          >
            새로고침
          </button>
        </div>

        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <select
              value={filters.action}
              onChange={(e) => setFilters({ ...filters, action: e.target.value })}
              className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white text-sm"
            >
              <option value="">모든 작업</option>
              <option value="login">로그인</option>
              <option value="create">생성</option>
              <option value="update">수정</option>
              <option value="delete">삭제</option>
              <option value="view">조회</option>
            </select>

            <select
              value={filters.resource}
              onChange={(e) => setFilters({ ...filters, resource: e.target.value })}
              className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white text-sm"
            >
              <option value="">모든 리소스</option>
              <option value="user">사용자</option>
              <option value="partner">파트너</option>
              <option value="energy_transaction">에너지 거래</option>
              <option value="system_setting">시스템 설정</option>
            </select>

            <select
              value={filters.dateRange}
              onChange={(e) => setFilters({ ...filters, dateRange: e.target.value })}
              className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white text-sm"
            >
              <option value="1">오늘</option>
              <option value="7">지난 7일</option>
              <option value="30">지난 30일</option>
              <option value="90">지난 90일</option>
            </select>
          </div>
        )}

        <div className="space-y-3">
          {logs.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              활동 로그가 없습니다.
            </div>
          ) : (
            logs.map((log) => (
              <div key={log.id} className="flex items-start space-x-3 p-3 bg-gray-900 rounded-lg">
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${_getActivityColor(log.action)}`}>
                  <span className="text-xs text-white">
                    {_getActivityIcon(log.action)}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-white">
                      <span className="font-medium">{log.userName}</span>
                      <span className="text-gray-300 ml-1">
                        {_formatActivityMessage(log)}
                      </span>
                    </p>
                    <span className="text-xs text-gray-400">
                      {_formatTimestamp(log.timestamp)}
                    </span>
                  </div>
                  {log.details && typeof log.details === 'object' && (
                    <p className="text-xs text-gray-400 mt-1">
                      {JSON.stringify(log.details, null, 2)}
                    </p>
                  )}
                  {log.ipAddress && (
                    <p className="text-xs text-gray-500 mt-1">
                      IP: {log.ipAddress}
                    </p>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {logs.length >= limit && (
          <div className="text-center mt-4">
            <button
              onClick={() => setLogs([])}
              className="text-blue-400 hover:text-blue-300 text-sm"
            >
              더 보기
            </button>
          </div>
        )}
      </div>
    </PermissionGuard>
  );
}
