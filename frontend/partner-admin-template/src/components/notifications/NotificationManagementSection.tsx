'use client'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Bell, Settings, AlertTriangle, CheckCircle, Info, Clock } from 'lucide-react'
import { PageHeader } from '@/components/common/PageHeader'
import { formatDate } from '@/lib/utils'

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

interface NotificationManagementSectionProps {
  notifications: Notification[]
  settings: NotificationSettings
  onMarkAsRead?: (id: string) => void
  onMarkAllAsRead?: () => void
  onSettingsChange?: (settings: NotificationSettings) => void
  onRefresh?: () => void
}

export function NotificationManagementSection({
  notifications,
  settings,
  onMarkAsRead,
  onMarkAllAsRead,
  onSettingsChange,
  onRefresh
}: NotificationManagementSectionProps) {
  const getPriorityColor = (priority: string) => {
    const colors = {
      low: 'bg-gray-100 text-gray-800',
      medium: 'bg-blue-100 text-blue-800',
      high: 'bg-yellow-100 text-yellow-800',
      critical: 'bg-red-100 text-red-800'
    }
    return colors[priority as keyof typeof colors] || colors.low
  }

  const getTypeIcon = (type: string) => {
    const icons = {
      system: Settings,
      security: AlertTriangle,
      transaction: CheckCircle,
      user: Info
    }
    return icons[type as keyof typeof icons] || Info
  }

  const unreadCount = notifications.filter(n => !n.read).length

  return (
    <div className="space-y-6">
      <PageHeader
        title="알림 관리"
        description="시스템 알림 및 메시지 관리"
        onRefresh={onRefresh}
      >
        <Button className="flex items-center gap-2" onClick={onMarkAllAsRead}>
          <CheckCircle className="w-4 h-4" />
          모두 읽음 표시
        </Button>
      </PageHeader>

      {/* 알림 요약 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">읽지 않은 알림</p>
                <p className="text-2xl font-bold text-red-600">{unreadCount}</p>
              </div>
              <Bell className="w-8 h-8 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">전체 알림</p>
                <p className="text-2xl font-bold text-blue-600">{notifications.length}</p>
              </div>
              <Bell className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">중요 알림</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {notifications.filter(n => n.priority === 'high' || n.priority === 'critical').length}
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-yellow-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">오늘 알림</p>
                <p className="text-2xl font-bold text-green-600">
                  {notifications.filter(n => {
                    const today = new Date().toISOString().split('T')[0]
                    return n.created_at.split('T')[0] === today
                  }).length}
                </p>
              </div>
              <Clock className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 알림 목록 */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>최근 알림</CardTitle>
              <CardDescription>시스템에서 발생한 알림 목록</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    알림이 없습니다.
                  </div>
                ) : (
                  notifications.map((notification) => {
                    const TypeIcon = getTypeIcon(notification.type)
                    return (
                      <div
                        key={notification.id}
                        className={`p-4 border rounded-lg transition-colors cursor-pointer hover:bg-gray-50 ${
                          !notification.read ? 'bg-blue-50 border-blue-200' : 'bg-white border-gray-200'
                        }`}
                        onClick={() => onMarkAsRead?.(notification.id)}
                      >
                        <div className="flex items-start gap-3">
                          <TypeIcon className="w-5 h-5 text-gray-600 mt-0.5" />
                          <div className="flex-1">
                            <div className="flex items-start justify-between">
                              <h4 className="font-medium text-gray-900">{notification.title}</h4>
                              <div className="flex items-center gap-2">
                                <Badge className={getPriorityColor(notification.priority)}>
                                  {notification.priority}
                                </Badge>
                                {!notification.read && (
                                  <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                                )}
                              </div>
                            </div>
                            <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
                            <div className="flex items-center justify-between mt-2">
                              <span className="text-xs text-gray-500">
                                {formatDate(notification.created_at)}
                              </span>
                              {notification.user_name && (
                                <span className="text-xs text-gray-500">
                                  사용자: {notification.user_name}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 알림 설정 */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>알림 설정</CardTitle>
              <CardDescription>알림 수신 방법 및 유형 설정</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">수신 방법</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-700">이메일 알림</span>
                      <Switch
                        checked={settings.email_enabled}
                        onCheckedChange={(checked) =>
                          onSettingsChange?.({ ...settings, email_enabled: checked })
                        }
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-700">푸시 알림</span>
                      <Switch
                        checked={settings.push_enabled}
                        onCheckedChange={(checked) =>
                          onSettingsChange?.({ ...settings, push_enabled: checked })
                        }
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-700">SMS 알림</span>
                      <Switch
                        checked={settings.sms_enabled}
                        onCheckedChange={(checked) =>
                          onSettingsChange?.({ ...settings, sms_enabled: checked })
                        }
                      />
                    </div>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h4 className="font-medium text-gray-900 mb-3">알림 유형</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-700">보안 알림</span>
                      <Switch
                        checked={settings.security_alerts}
                        onCheckedChange={(checked) =>
                          onSettingsChange?.({ ...settings, security_alerts: checked })
                        }
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-700">거래 알림</span>
                      <Switch
                        checked={settings.transaction_alerts}
                        onCheckedChange={(checked) =>
                          onSettingsChange?.({ ...settings, transaction_alerts: checked })
                        }
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-700">사용자 알림</span>
                      <Switch
                        checked={settings.user_alerts}
                        onCheckedChange={(checked) =>
                          onSettingsChange?.({ ...settings, user_alerts: checked })
                        }
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-700">시스템 점검</span>
                      <Switch
                        checked={settings.system_maintenance}
                        onCheckedChange={(checked) =>
                          onSettingsChange?.({ ...settings, system_maintenance: checked })
                        }
                      />
                    </div>
                  </div>
                </div>

                <div className="pt-4">
                  <Button className="w-full">설정 저장</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
