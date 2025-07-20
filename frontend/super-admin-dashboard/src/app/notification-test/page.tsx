'use client';

import React from 'react';
import { notificationManager } from '@/lib/notification-manager';
import { NotificationPriority, NotificationChannel } from '@/types/notification';
import { Button, Section } from '@/components/ui/DarkThemeComponents';
import { BasePage } from '@/components/ui/BasePage';

export default function NotificationTestPage() {
  const addTestNotification = (priority: NotificationPriority, channel: NotificationChannel) => {
    const testMessages: Record<NotificationPriority, string> = {
      [NotificationPriority.CRITICAL]: '🚨 위험: 시스템 치명적 오류가 발생했습니다.',
      [NotificationPriority.HIGH]: '⚠️ 긴급: 시스템 보안 경고가 발생했습니다.',
      [NotificationPriority.MEDIUM]: '🔔 알림: 새로운 파트너 가입 요청이 있습니다.',
      [NotificationPriority.LOW]: '💡 정보: 일일 리포트가 생성되었습니다.'
    };

    notificationManager.addNotification({
      title: `${priority.toUpperCase()} 우선순위 테스트`,
      message: testMessages[priority] || '테스트 알림입니다.',
      priority,
      channel,
      type: 'info'
    });
  };

  const clearAllNotifications = () => {
    notificationManager.clearAll();
  };

  return (
    <BasePage 
      title="🔔 알림 테스트"
      description="알림 시스템의 다양한 기능을 테스트할 수 있습니다."
    >
      <Section title="빠른 테스트">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <Button 
            variant="danger"
            onClick={() => addTestNotification(NotificationPriority.HIGH, NotificationChannel.SYSTEM)}
            className="w-full"
          >
            🚨 높은 우선순위
          </Button>
          <Button 
            variant="primary"
            onClick={() => addTestNotification(NotificationPriority.MEDIUM, NotificationChannel.PARTNER)}
            className="w-full"
          >
            🔔 보통 우선순위
          </Button>
          <Button 
            variant="secondary"
            onClick={() => addTestNotification(NotificationPriority.LOW, NotificationChannel.TRADING)}
            className="w-full"
          >
            💡 낮은 우선순위
          </Button>
        </div>
        
        <div className="flex justify-center">
          <Button 
            variant="outline"
            onClick={clearAllNotifications}
            className="w-full md:w-auto"
          >
            🗑️ 모든 알림 삭제
          </Button>
        </div>
      </Section>

      <Section title="채널별 테스트">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Button 
            variant="secondary"
            onClick={() => addTestNotification(NotificationPriority.MEDIUM, NotificationChannel.SYSTEM)}
            className="w-full"
          >
            🔧 시스템
          </Button>
          <Button 
            variant="secondary"
            onClick={() => addTestNotification(NotificationPriority.MEDIUM, NotificationChannel.SECURITY)}
            className="w-full"
          >
            🛡️ 보안
          </Button>
          <Button 
            variant="secondary"
            onClick={() => addTestNotification(NotificationPriority.MEDIUM, NotificationChannel.TRADING)}
            className="w-full"
          >
            💱 거래
          </Button>
          <Button 
            variant="secondary"
            onClick={() => addTestNotification(NotificationPriority.MEDIUM, NotificationChannel.PARTNER)}
            className="w-full"
          >
            🤝 파트너
          </Button>
          <Button 
            variant="secondary"
            onClick={() => addTestNotification(NotificationPriority.MEDIUM, NotificationChannel.COMPLIANCE)}
            className="w-full"
          >
            📋 컴플라이언스
          </Button>
        </div>
      </Section>

      <Section title="우선순위별 테스트">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Button 
            variant="danger"
            onClick={() => addTestNotification(NotificationPriority.CRITICAL, NotificationChannel.SECURITY)}
            className="w-full"
          >
            🚨 치명적
          </Button>
          <Button 
            variant="danger"
            onClick={() => addTestNotification(NotificationPriority.HIGH, NotificationChannel.SYSTEM)}
            className="w-full"
          >
            ⚠️ 높음
          </Button>
          <Button 
            variant="primary"
            onClick={() => addTestNotification(NotificationPriority.MEDIUM, NotificationChannel.PARTNER)}
            className="w-full"
          >
            🔔 보통
          </Button>
          <Button 
            variant="secondary"
            onClick={() => addTestNotification(NotificationPriority.LOW, NotificationChannel.TRADING)}
            className="w-full"
          >
            💡 낮음
          </Button>
        </div>
      </Section>
    </BasePage>
  );
}
