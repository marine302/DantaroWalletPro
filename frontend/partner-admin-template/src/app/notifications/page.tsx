'use client'

import { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { NotificationManagementSection } from '@/components/notifications/NotificationManagementSection'

interface Notification {
  id: string
  type: 'system' | 'security' | 'transaction' | 'user'
  title: string
  message: string
  priority: 'low' | 'medium' | 'high' | 'critical'
  read: boolean
  created_at: string
  user_id?: string
  user_name?: string
}

interface NotificationSettings {
  email_enabled: boolean
  push_enabled: boolean
  sms_enabled: boolean
  security_alerts: boolean
  transaction_alerts: boolean
  user_alerts: boolean
  system_maintenance: boolean
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([
    {
      id: '1',
      type: 'security',
      title: '보안 알림: 새로운 로그인 감지',
      message: '알 수 없는 기기에서 로그인이 감지되었습니다. IP: 192.168.1.100',
      priority: 'high',
      read: false,
      created_at: '2024-07-20T09:30:00Z',
      user_id: 'user123',
      user_name: 'john_doe'
    },
    {
      id: '2',
      type: 'transaction',
      title: '대량 출금 요청',
      message: '1,000 TRX 이상의 출금 요청이 5건 접수되었습니다.',
      priority: 'medium',
      read: false,
      created_at: '2024-07-20T08:15:00Z'
    },
    {
      id: '3',
      type: 'system',
      title: '시스템 점검 예정',
      message: '내일 새벽 2시부터 4시까지 시스템 점검이 예정되어 있습니다.',
      priority: 'low',
      read: true,
      created_at: '2024-07-19T16:00:00Z'
    },
    {
      id: '4',
      type: 'user',
      title: '신규 사용자 등록',
      message: '오늘 24명의 신규 사용자가 등록되었습니다.',
      priority: 'low',
      read: true,
      created_at: '2024-07-19T23:59:00Z'
    },
    {
      id: '5',
      type: 'security',
      title: '비정상적인 API 호출 감지',
      message: 'API 호출 빈도가 평소보다 300% 증가했습니다.',
      priority: 'critical',
      read: false,
      created_at: '2024-07-20T07:45:00Z'
    }
  ])

  const [settings, setSettings] = useState<NotificationSettings>({
    email_enabled: true,
    push_enabled: true,
    sms_enabled: false,
    security_alerts: true,
    transaction_alerts: true,
    user_alerts: false,
    system_maintenance: true
  })

  const handleMarkAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(notification =>
        notification.id === id ? { ...notification, read: true } : notification
      )
    )
  }

  const handleMarkAllAsRead = () => {
    setNotifications(prev =>
      prev.map(notification => ({ ...notification, read: true }))
    )
  }

  const handleSettingsChange = (newSettings: NotificationSettings) => {
    setSettings(newSettings)
    // TODO: API 호출하여 설정 저장
    console.log('Settings updated:', newSettings)
  }

  const handleRefresh = () => {
    // TODO: 알림 데이터 새로고침
    console.log('Refreshing notifications...')
  }

  return (
    <Sidebar>
      <div className="container mx-auto p-6">
        <NotificationManagementSection
          notifications={notifications}
          settings={settings}
          onMarkAsRead={handleMarkAsRead}
          onMarkAllAsRead={handleMarkAllAsRead}
          onSettingsChange={handleSettingsChange}
          onRefresh={handleRefresh}
        />
      </div>
    </Sidebar>
  )
}
