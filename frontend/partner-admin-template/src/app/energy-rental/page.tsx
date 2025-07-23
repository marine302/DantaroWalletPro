'use client'

import React from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { EnergyRentalManagementSection } from '@/components/energy-rental/EnergyRentalManagementSection'
import { useEnergyRentalOverview, useBackendConnection } from '@/lib/hooks/useEnergyRentalHooks'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, AlertTriangle, Wifi, WifiOff } from 'lucide-react'

export default function EnergyRentalPage() {
  const { isConnected } = useBackendConnection()
  const {
    plans,
    usage,
    allocation,
    pools,
    system,
    isLoading,
    hasError,
    refetch
  } = useEnergyRentalOverview()

  // 백엔드 연결 상태 표시
  const ConnectionStatus = () => (
    <div className="flex items-center gap-2 text-sm">
      {isConnected === null ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : isConnected ? (
        <>
          <Wifi className="w-4 h-4 text-green-500" />
          <span className="text-green-600">백엔드 연결됨</span>
        </>
      ) : (
        <>
          <WifiOff className="w-4 h-4 text-red-500" />
          <span className="text-red-600">백엔드 연결 실패 (목 데이터 사용 중)</span>
        </>
      )}
    </div>
  )

  if (isLoading) {
    return (
      <Sidebar>
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
            <p className="text-gray-600">에너지 렌탈 데이터를 불러오는 중...</p>
          </div>
        </div>
      </Sidebar>
    )
  }
  return (
    <Sidebar>
      <div className="p-8 space-y-6">
        {/* 헤더 */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">에너지 렌탈 관리</h1>
            <p className="text-gray-600 mt-1">Super Admin에서 에너지를 렌탈하여 사용자에게 제공</p>
          </div>
          <ConnectionStatus />
        </div>

        {/* 백엔드 연결 상태 알림 */}
        {isConnected === false && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              백엔드 서버에 연결할 수 없습니다. 목 데이터를 사용하여 개발 중입니다.
              백엔드 준비 완료 후 실제 데이터로 자동 전환됩니다.
            </AlertDescription>
          </Alert>
        )}

        {/* 에러 상태 */}
        {hasError && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              데이터를 불러오는 중 오류가 발생했습니다.
              <button 
                onClick={refetch}
                className="ml-2 underline hover:no-underline"
              >
                다시 시도
              </button>
            </AlertDescription>
          </Alert>
        )}

        {/* 에너지 렌탈 관리 섹션 */}
        <EnergyRentalManagementSection
          plans={plans}
          usage={usage}
          allocation={allocation}
          pools={pools}
          system={system}
          isBackendConnected={isConnected === true}
        />
      </div>
    </Sidebar>
  )
}