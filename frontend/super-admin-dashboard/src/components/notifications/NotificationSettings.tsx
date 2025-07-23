'use client';

import React, { useState, useEffect } from 'react';
import { notificationManager } from '@/lib/notification-manager';
import { NotificationSettings, NotificationPriority, NotificationChannel } from '@/types/notification';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface NotificationSettingsProps {
  onClose?: () => void;
}

export const NotificationSettingsComponent: React.FC<NotificationSettingsProps> = ({
  onClose
}) => {
  const [settings, setSettings] = useState<NotificationSettings>(notificationManager.getSettings());
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    const _currentSettings = notificationManager.getSettings();
    setSettings(currentSettings);
  }, []);

  const _handleSettingChange = (key: keyof NotificationSettings, value: any) => {
    const _newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    setHasChanges(true);
  };

  const _handlePriorityChange = (priority: NotificationPriority, enabled: boolean) => {
    const _newPriorities = { ...settings.priorities, [priority]: enabled };
    handleSettingChange('priorities', newPriorities);
  };

  const _handleChannelChange = (channel: NotificationChannel, enabled: boolean) => {
    const _newChannels = { ...settings.channels, [channel]: enabled };
    handleSettingChange('channels', newChannels);
  };

  const _handleSave = () => {
    notificationManager.updateSettings(settings);
    setHasChanges(false);
    onClose?.();
  };

  const _handleReset = () => {
    const _currentSettings = notificationManager.getSettings();
    setSettings(currentSettings);
    setHasChanges(false);
  };

  const _requestNotificationPermission = async () => {
    if (!('Notification' in window)) {
      alert('이 브라우저는 데스크톱 알림을 지원하지 않습니다.');
      return;
    }

    const _permission = await Notification.requestPermission();
    if (permission === 'granted') {
      handleSettingChange('pushEnabled', true);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          알림 설정
        </h2>
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

      {/* 기본 설정 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          기본 설정
        </h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                알림 활성화
              </label>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                모든 알림을 활성화하거나 비활성화합니다
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.enabled}
                onChange={(e) => handleSettingChange('enabled', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                사운드 알림
              </label>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                새 알림 시 사운드를 재생합니다
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.soundEnabled}
                onChange={(e) => handleSettingChange('soundEnabled', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                데스크톱 푸시 알림
              </label>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                브라우저 데스크톱 알림을 활성화합니다
              </p>
            </div>
            <div className="flex items-center space-x-2">
              {!settings.pushEnabled && Notification.permission === 'default' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={requestNotificationPermission}
                  className="text-xs"
                >
                  권한 요청
                </Button>
              )}
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.pushEnabled}
                  onChange={(e) => handleSettingChange('pushEnabled', e.target.checked)}
                  disabled={Notification.permission !== 'granted'}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600 peer-disabled:opacity-50"></div>
              </label>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                자동 읽음 처리
              </label>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                3초 후 자동으로 읽음 처리합니다
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.autoMarkAsRead}
                onChange={(e) => handleSettingChange('autoMarkAsRead', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>
      </Card>

      {/* 우선순위 설정 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          우선순위별 알림 설정
        </h3>
        <div className="space-y-3">
          {Object.values(NotificationPriority).map((priority) => (
            <div key={priority} className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${
                  priority === NotificationPriority.CRITICAL ? 'bg-red-500' :
                  priority === NotificationPriority.HIGH ? 'bg-orange-500' :
                  priority === NotificationPriority.MEDIUM ? 'bg-yellow-500' :
                  'bg-green-500'
                }`} />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
                  {priority}
                </span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.priorities[priority]}
                  onChange={(e) => handlePriorityChange(priority, e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              </label>
            </div>
          ))}
        </div>
      </Card>

      {/* 채널별 설정 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          채널별 알림 설정
        </h3>
        <div className="space-y-3">
          {Object.values(NotificationChannel).map((channel) => (
            <div key={channel} className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
                {channel.replace('_', ' ')}
              </span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.channels[channel]}
                  onChange={(e) => handleChannelChange(channel, e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              </label>
            </div>
          ))}
        </div>
      </Card>

      {/* 고급 설정 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          고급 설정
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              최대 활성 알림 수
            </label>
            <input
              type="number"
              min="1"
              max="50"
              value={settings.maxActiveNotifications}
              onChange={(e) => handleSettingChange('maxActiveNotifications', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              히스토리 보관 기간 (일)
            </label>
            <input
              type="number"
              min="1"
              max="365"
              value={settings.historyRetentionDays}
              onChange={(e) => handleSettingChange('historyRetentionDays', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
          </div>
        </div>
      </Card>

      {/* 저장 버튼 */}
      <div className="flex justify-end space-x-3">
        <Button
          variant="outline"
          onClick={handleReset}
          disabled={!hasChanges}
        >
          초기화
        </Button>
        <Button
          onClick={handleSave}
          disabled={!hasChanges}
          className="bg-blue-600 hover:bg-blue-700"
        >
          설정 저장
        </Button>
      </div>
    </div>
  );
};
