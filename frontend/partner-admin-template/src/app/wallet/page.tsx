'use client'

import { Sidebar } from '@/components/layout/Sidebar'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function WalletPage() {
  return (
    <Sidebar>
      <div className="container mx-auto p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">지갑 관리</h1>
          <p className="text-gray-600 mt-1">TronLink 지갑 연동 및 관리</p>
        </div>
        
        <Card>
          <CardHeader>
            <CardTitle>지갑 관리 페이지</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">TronLink 지갑 연동 및 관리 기능이 여기에 구현됩니다.</p>
            <p className="text-sm text-gray-500 mt-2">🚧 Phase 2에서 구현 예정</p>
          </CardContent>
        </Card>
      </div>
    </Sidebar>
  )
}
