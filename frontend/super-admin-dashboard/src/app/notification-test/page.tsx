'use client';

import React from 'react';
import { notificationManager } from '@/lib/notification-manager';
import { NotificationPriority, NotificationChannel } from '@/types/notification';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { BasePage } from '@/components/ui/BasePage';

export default function NotificationTestPage() {
  const addTestNotification = (priority: NotificationPriority, channel: NotificationChannel) => {
    const testMessages = {
      [NotificationPriority.CRITICAL]: {
        title: '긴급: 시스템 보안 위험',
        message: '무단 접근 시도가 감지되었습니다. 즉시 확인이 필요합니다.'
      },
      [NotificationPriority.HIGH]: {
        title: '높은 우선순위: 거래량 급증',
        message: '현재 거래량이 평균의 300%를 초과했습니다.'
      },
      [NotificationPriority.MEDIUM]: {
        title: '중간 우선순위: 파트너 승인 대기',
        message: '새로운 파트너 신청이 승인을 기다리고 있습니다.'
      },
      [NotificationPriority.LOW]: {
        title: '낮은 우선순위: 시스템 업데이트',
        message: '시스템 정기 업데이트가 예정되어 있습니다.'
      }
    };

    notificationManager.addNotification({
      ...testMessages[priority],
      priority,
      channel,
      type: 'info',
      actions: [{
        label: '확인',
        action: () => console.log('알림 확인됨')
      }]
    });
  };

  const addBulkNotifications = () => {
    const notifications = [
      {
        title: '새로운 사용자 등록',
        message: 'user@example.com이 새로 가입했습니다.',
        priority: NotificationPriority.LOW,
        channel: NotificationChannel.SYSTEM
      },
      {
        title: '에너지 거래 완료',
        message: '1,000 kWh 에너지 거래가 성공적으로 완료되었습니다.',
        priority: NotificationPriority.MEDIUM,
        channel: NotificationChannel.TRADING
      },
      {
        title: '보안 알림',
        message: '의심스러운 로그인 시도가 감지되었습니다.',
        priority: NotificationPriority.HIGH,
        channel: NotificationChannel.SECURITY
      }
    ];

    notifications.forEach(notification => {
      notificationManager.addNotification({
        ...notification,
        type: 'info',
        actions: []
      });
    });
  };

  const testSounds = () => {
    // 각 우선순위별로 순차적으로 테스트
    setTimeout(() => addTestNotification(NotificationPriority.LOW, NotificationChannel.SYSTEM), 0);
    setTimeout(() => addTestNotification(NotificationPriority.MEDIUM, NotificationChannel.TRADING), 1000);
    setTimeout(() => addTestNotification(NotificationPriority.HIGH, NotificationChannel.SECURITY), 2000);
    setTimeout(() => addTestNotification(NotificationPriority.CRITICAL, NotificationChannel.SECURITY), 3000);
  };

  return (
    <BasePage
      title="알림 시스템 테스트"
      description="알림 시스템의 다양한 기능을 테스트해보세요"
    >
      <div className="space-y-6">
        {/* 기본 테스트 */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">기본 알림 테스트</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button
              onClick={() => addTestNotification(NotificationPriority.CRITICAL, NotificationChannel.SECURITY)}
              className="bg-red-600 hover:bg-red-700"
            >
              긴급 알림
            </Button>
            <Button
              onClick={() => addTestNotification(NotificationPriority.HIGH, NotificationChannel.TRADING)}
              className="bg-orange-600 hover:bg-orange-700"
            >
              높은 우선순위
            </Button>
            <Button
              onClick={() => addTestNotification(NotificationPriority.MEDIUM, NotificationChannel.PARTNER)}
              className="bg-yellow-600 hover:bg-yellow-700"
            >
              중간 우선순위
            </Button>
            <Button
              onClick={() => addTestNotification(NotificationPriority.LOW, NotificationChannel.SYSTEM)}
              className="bg-green-600 hover:bg-green-700"
            >
              낮은 우선순위
            </Button>
          </div>
        </Card>

        {/* 채널별 테스트 */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">채널별 알림 테스트</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <Button
              onClick={() => addTestNotification(NotificationPriority.MEDIUM, NotificationChannel.SYSTEM)}
              variant="outline"
            >
              ⚙️ 시스템
            </Button>
            <Button
              onClick={() => addTestNotification(NotificationPriority.HIGH, NotificationChannel.SECURITY)}
              variant="outline"
            >
              🔒 보안
            </Button>
            <Button
              onClick={() => addTestNotification(NotificationPriority.MEDIUM, NotificationChannel.TRADING)}
              variant="outline"
            >
              💹 거래
            </Button>
            <Button
              onClick={() => addTestNotification(NotificationPriority.LOW, NotificationChannel.PARTNER)}
              variant="outline"
            >
              🤝 파트너
            </Button>
            <Button
              onClick={() => addTestNotification(NotificationPriority.MEDIUM, NotificationChannel.COMPLIANCE)}
              variant="outline"
            >
              📋 컴플라이언스
            </Button>
          </div>
        </Card>

        {/* 대량 테스트 */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">고급 테스트</h3>
          <div className="flex flex-wrap gap-4">
            <Button
              onClick={addBulkNotifications}
              variant="outline"
            >
              📦 대량 알림 추가 (3개)
            </Button>
            <Button
              onClick={testSounds}
              variant="outline"
            >
              🔊 사운드 테스트 (순차적)
            </Button>
            <Button
              onClick={() => notificationManager.clearAll()}
              variant="outline"
              className="text-red-600 hover:text-red-700"
            >
              🗑️ 모든 알림 지우기
            </Button>
          </div>
        </Card>

        {/* 설정 테스트 */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">설정 테스트</h3>
          <div className="flex flex-wrap gap-4">
            <Button
              onClick={() => {
                const settings = notificationManager.getSettings();
                notificationManager.updateSettings({ ...settings, soundEnabled: !settings.soundEnabled });
                alert(`사운드 ${settings.soundEnabled ? '비활성화' : '활성화'}됨`);
              }}
              variant="outline"
            >
              🔇 사운드 토글
            </Button>
            <Button
              onClick={() => {
                if (Notification.permission === 'default') {
                  Notification.requestPermission().then(permission => {
                    alert(`푸시 알림 권한: ${permission}`);
                  });
                } else {
                  alert(`현재 푸시 알림 권한: ${Notification.permission}`);
                }
              }}
              variant="outline"
            >
              📱 푸시 알림 권한 확인
            </Button>
          </div>
        </Card>

        {/* 현재 상태 */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">현재 상태</h3>
          <div className="space-y-2 text-sm">
            <p>읽지 않은 알림: <span className="font-bold">{notificationManager.getUnreadCount()}개</span></p>
            <p>총 활성 알림: <span className="font-bold">{notificationManager.getActiveNotifications().length}개</span></p>
            <p>사운드 설정: <span className="font-bold">{notificationManager.getSettings().soundEnabled ? '활성화' : '비활성화'}</span></p>
            <p>푸시 알림 권한: <span className="font-bold">{typeof window !== 'undefined' ? Notification.permission : 'N/A'}</span></p>
          </div>
        </Card>

        {/* 사용법 안내 */}
        <Card className="p-6 bg-blue-50 dark:bg-blue-900/20">
          <h3 className="text-lg font-semibold mb-4 text-blue-900 dark:text-blue-100">사용법</h3>
          <div className="text-sm text-blue-800 dark:text-blue-200 space-y-2">
            <p>1. 우측 상단의 🔔 알림 벨을 클릭하여 알림 센터를 열어보세요</p>
            <p>2. 알림 센터에서 ⚙️ 버튼을 클릭하여 설정을 변경할 수 있습니다</p>
            <p>3. 📋 버튼을 클릭하여 알림 히스토리를 확인할 수 있습니다</p>
            <p>4. 각 우선순위별로 다른 사운드가 재생됩니다</p>
            <p>5. 브라우저에서 데스크톱 알림 권한을 허용하면 푸시 알림도 받을 수 있습니다</p>
          </div>
        </Card>
      </div>
    </BasePage>
  );
}
