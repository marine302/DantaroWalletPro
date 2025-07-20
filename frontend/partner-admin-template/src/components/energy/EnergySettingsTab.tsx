'use client'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { EnergySettings } from '@/types'

interface EnergySettingsTabProps {
  settings?: EnergySettings
  onSave?: (settings: EnergySettings) => void
}

export function EnergySettingsTab({ settings, onSave }: EnergySettingsTabProps) {
  const defaultSettings: EnergySettings = {
    default_price_per_unit: 0.000350,
    max_rental_hours: 72,
    auto_refill_enabled: true,
    dynamic_pricing_enabled: false,
    auto_maintenance_enabled: true
  }

  const currentSettings = settings || defaultSettings

  return (
    <Card>
      <CardHeader>
        <CardTitle>에너지 풀 설정</CardTitle>
        <CardDescription>에너지 풀 운영 및 가격 정책 설정</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">기본 설정</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  기본 에너지 단가 (TRX)
                </label>
                <Input 
                  type="number" 
                  step="0.000001"
                  placeholder="0.000350"
                  defaultValue={currentSettings.default_price_per_unit.toString()}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  최대 대여 기간 (시간)
                </label>
                <Input 
                  type="number"
                  placeholder="72"
                  defaultValue={currentSettings.max_rental_hours.toString()}
                />
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">자동 관리</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">자동 풀 보충</p>
                  <p className="text-sm text-gray-500">에너지 용량이 20% 이하로 떨어지면 자동 보충</p>
                </div>
                <input 
                  type="checkbox" 
                  defaultChecked={currentSettings.auto_refill_enabled}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" 
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">동적 가격 조정</p>
                  <p className="text-sm text-gray-500">수요에 따라 에너지 단가 자동 조정</p>
                </div>
                <input 
                  type="checkbox" 
                  defaultChecked={currentSettings.dynamic_pricing_enabled}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" 
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">점검 모드 자동 전환</p>
                  <p className="text-sm text-gray-500">문제 감지시 자동으로 점검 모드로 전환</p>
                </div>
                <input 
                  type="checkbox" 
                  defaultChecked={currentSettings.auto_maintenance_enabled}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" 
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3">
            <Button variant="outline">취소</Button>
            <Button onClick={() => onSave?.(currentSettings)}>설정 저장</Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
