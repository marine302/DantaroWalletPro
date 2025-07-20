'use client'

import { Sidebar } from '@/components/layout/Sidebar'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function NotificationsPage() {
  return (
    <Sidebar>
      <div className="container mx-auto p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">알림 관리</h1>
          <p className="text-gray-600 dark:text-gray-300 mt-1">시스템 알림 및 메시지 관리</p>
        </div>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-gray-900 dark:text-gray-100">알림 관리 페이지</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 bg-gray-50 dark:bg-gray-800 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600">
              <div className="mb-4">
                <svg className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 17h5l-5 5 5-5H9.5a9.5 9.5 0 110-19h11.5m-5 4-5 5 5-5z"/>
                </svg>
              </div>
              <p className="text-lg font-medium text-gray-600 dark:text-gray-300">알림 관리 기능 준비 중</p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">🚧 Phase 2에서 구현 예정</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </Sidebar>
  )
}
