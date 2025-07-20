'use client'

import { Sidebar } from '@/components/layout/Sidebar'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function WalletPage() {
  return (
    <Sidebar>
      <div className="container mx-auto p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">지갑 관리</h1>
          <p className="text-gray-600 dark:text-gray-300 mt-1">TronLink 지갑 연동 및 관리</p>
        </div>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-gray-900 dark:text-gray-100">지갑 관리 페이지</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 bg-gray-50 dark:bg-gray-800 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600">
              <div className="mb-4">
                <svg className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"/>
                </svg>
              </div>
              <p className="text-lg font-medium text-gray-600 dark:text-gray-300">지갑 관리 기능 준비 중</p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">🚧 Phase 2에서 구현 예정</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </Sidebar>
  )
}
