'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Bell, AlertTriangle, TrendingUp } from 'lucide-react'
import { Notification } from '@/types'
import { formatDate } from '@/lib/utils'

interface NotificationCenterProps {
  notifications: Notification[]
  onViewAll: () => void
}

export function NotificationCenter({ notifications, onViewAll }: NotificationCenterProps) {
  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />
      case 'success':
        return <TrendingUp className="h-4 w-4 text-green-600" />
      case 'info':
        return <Bell className="h-4 w-4 text-blue-600" />
      case 'error':
        return <AlertTriangle className="h-4 w-4 text-red-600" />
      default:
        return <Bell className="h-4 w-4 text-gray-600" />
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>알림 센터</CardTitle>
        <CardDescription>
          최근 시스템 알림 및 경고
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {notifications.slice(0, 3).map((notification) => (
            <div 
              key={notification.id}
              className={`flex items-start gap-3 p-3 rounded-lg border ${
                notification.read ? 'bg-gray-50 border-gray-200' : 'bg-blue-50 border-blue-200'
              }`}
            >
              {getNotificationIcon(notification.type)}
              <div className="flex-1">
                <div className="font-medium">{notification.title}</div>
                <div className="text-sm text-gray-600">{notification.message}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {formatDate(notification.timestamp)}
                </div>
              </div>
              {!notification.read && (
                <div className="h-2 w-2 bg-blue-600 rounded-full" />
              )}
            </div>
          ))}
        </div>
        <div className="mt-4 pt-4 border-t">
          <Button variant="outline" className="w-full" onClick={onViewAll}>
            모든 알림 보기
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
